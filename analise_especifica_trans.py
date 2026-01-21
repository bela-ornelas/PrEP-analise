import pandas as pd
import numpy as np
import sys
import os

# Tentar importar statsmodels
try:
    import statsmodels.formula.api as smf
    import statsmodels.api as sm
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

# Adiciona o diretório atual ao path
sys.path.append(os.getcwd())

from src.data_loader import carregar_bases
from src.cleaning import clean_disp_df, process_cadastro
# Importar função correta para cálculo de populações e enriquecimento
try:
    from src.preprocessing import calculate_population_groups, enrich_disp_data
except ImportError:
    print("ERRO CRÍTICO: Não foi possível importar calculate_population_groups ou enrich_disp_data")
    sys.exit(1)

def classificar_comportamento(df_disp, data_fechamento):
    """
    Classifica cada paciente em: 'Sustentado', 'Cíclico', 'Drop-out'.
    """
    print("Classificando comportamento longitudinal...")
    hoje_dt = pd.to_datetime(data_fechamento).normalize()
    
    # --- FILTRO 1: Remover quem já fez PrEP Sob Demanda ---
    if 'tp_modalidade' in df_disp.columns:
        modalidades = df_disp['tp_modalidade'].astype(str).str.lower()
        sob_demanda_mask = modalidades.str.contains('demanda')
        pacs_sob_demanda = df_disp.loc[sob_demanda_mask, 'codigo_pac_eleito'].unique()
        print(f"Excluindo {len(pacs_sob_demanda)} usuários com histórico de PrEP Sob Demanda.")
        df_disp = df_disp[~df_disp['codigo_pac_eleito'].isin(pacs_sob_demanda)]

    # --- FILTRO 2: Remover Iniciantes Recentes (< 6 meses de seguimento) ---
    data_corte_inicio = hoje_dt - pd.to_timedelta(180, unit='D')
    grp_inicio = df_disp.groupby('codigo_pac_eleito')['dt_disp'].min()
    pacs_recentes = grp_inicio[grp_inicio > data_corte_inicio].index
    print(f"Excluindo {len(pacs_recentes)} usuários iniciantes recentes (início após {data_corte_inicio.date()}).")
    df_disp = df_disp[~df_disp['codigo_pac_eleito'].isin(pacs_recentes)]
    
    # Ordenar
    df_disp = df_disp.sort_values(['codigo_pac_eleito', 'dt_disp'])
    
    # Calcular validade
    if 'duracao_sum' not in df_disp.columns:
        duracao = df_disp['duracao'] if 'duracao' in df_disp.columns else 30
    else:
        duracao = df_disp['duracao_sum']
        
    df_disp['valid_until'] = df_disp['dt_disp'] + pd.to_timedelta(duracao * 1.4, unit='D')
    
    # Gaps > 30 dias
    df_disp['prev_valid_until'] = df_disp.groupby('codigo_pac_eleito')['valid_until'].shift(1)
    gap_margin = pd.to_timedelta(30, unit='D')
    df_disp['has_gap'] = df_disp['dt_disp'] > (df_disp['prev_valid_until'] + gap_margin)
    
    # Identificar perfis
    pacientes_ciclicos = df_disp.loc[df_disp['has_gap'], 'codigo_pac_eleito'].unique()
    
    last_disp = df_disp.sort_values('dt_disp').drop_duplicates('codigo_pac_eleito', keep='last')
    
    # Critério de Abandono (180 dias)
    limite_abandono = hoje_dt - pd.to_timedelta(180, unit='D')
    is_active_retention = last_disp['valid_until'] >= limite_abandono
    pacientes_ativos_now = last_disp.loc[is_active_retention, 'codigo_pac_eleito'].unique()
    
    # Montar DataFrame
    all_pacs = df_disp['codigo_pac_eleito'].unique()
    classification = pd.DataFrame({'codigo_pac_eleito': all_pacs})
    
    conditions = [
        classification['codigo_pac_eleito'].isin(pacientes_ciclicos),
        classification['codigo_pac_eleito'].isin(pacientes_ativos_now)
    ]
    # Nomes simplificados para a regressão
    choices = ['Cyclic', 'Sustained']
    
    classification['perfil_uso'] = np.select(conditions, choices, default='Discontinued')
    
    # Adicionar Região
    regiao_map = df_disp.drop_duplicates('codigo_pac_eleito', keep='last')[['codigo_pac_eleito', 'regiao_UDM']]
    classification = classification.merge(regiao_map, on='codigo_pac_eleito', how='left')
    
    # Adicionar Ano de Início
    first_disp = df_disp.sort_values('dt_disp').drop_duplicates('codigo_pac_eleito', keep='first')[['codigo_pac_eleito', 'dt_disp']]
    first_disp['ano_inicio'] = first_disp['dt_disp'].dt.year
    classification = classification.merge(first_disp[['codigo_pac_eleito', 'ano_inicio']], on='codigo_pac_eleito', how='left')

    return classification

def executar_regressao_multinomial(df):
    if not HAS_STATSMODELS:
        return None

    print("\n" + "="*80)
    print("REGRESSÃO LOGÍSTICA MULTINOMIAL (ROBUSTA)")
    print("Desfecho: Perfil de Uso (Ref: Sustained)")
    print("="*80)

    # 1. Preparação dos Dados
    vars_model = ['perfil_uso', 'Pop_genero_pratica', 'faixa_etaria', 'raca4_cat', 'escol4', 'regiao_UDM', 'ano_inicio']
    
    df_reg = df[vars_model].copy().dropna()
    
    # Filtrar 'Outros' e categorias irrelevantes
    df_reg = df_reg[~df_reg['Pop_genero_pratica'].isin(['Outros', 'Ignorado'])]
    df_reg = df_reg[~df_reg['raca4_cat'].isin(['Ignorada/Não informada'])]
    
    # 2. Simplificar Nomes
    pop_map = {
        'Gays e outros HSH cis': 'HSH', 'Homens heterossexuais cis': 'HeteroCis',
        'Mulheres cis': 'MulherCis', 'Mulheres trans': 'MulherTrans',
        'Homens trans': 'HomemTrans', 'Travestis': 'Travesti', 'Não bináries': 'NaoBinario'
    }
    df_reg['Pop'] = df_reg['Pop_genero_pratica'].map(pop_map).fillna('Outros')
    
    edu_map = {
        '12 ou mais anos': 'High', 'De 8 a 11 anos': 'Medium',
        'De 4 a 7 anos': 'Low', 'Sem educação formal a 3 anos': 'None', 'De 1 a 3 anos': 'None'
    }
    df_reg['Edu'] = df_reg['escol4'].map(edu_map)
    
    race_map = {'Branca/Amarela': 'White', 'Preta': 'Black', 'Parda': 'Brown', 'Indígena': 'Indig'}
    df_reg['Race'] = df_reg['raca4_cat'].map(race_map)
    
    df_reg['Region'] = df_reg['regiao_UDM']
    df_reg['Age'] = df_reg['faixa_etaria']
    df_reg['YearStart'] = df_reg['ano_inicio']

    # 3. Fit do Modelo
    cat_order = ['Sustained', 'Cyclic', 'Discontinued']
    df_reg['perfil_uso'] = pd.Categorical(df_reg['perfil_uso'], categories=cat_order, ordered=True)
    df_reg['y'] = df_reg['perfil_uso'].cat.codes # 0, 1, 2
    
    formula = (
        "y ~ C(Pop, Treatment('HSH')) + C(Age, Treatment('30-39')) + "
        "C(Race, Treatment('White')) + C(Edu, Treatment('High')) + "
        "C(Region, Treatment('Sudeste')) + C(YearStart)" 
    )
    
    results_list = []

    try:
        model = smf.mnlogit(formula, df_reg)
        result = model.fit(disp=0, method='bfgs', maxiter=5000)
        
        print("\n>>> RESULTADOS: ADJUSTED ODDS RATIOS (aOR) [Ref: Sustained Use] <<<")
        
        params = np.exp(result.params)
        conf = np.exp(result.conf_int())
        pvalues = result.pvalues
        
        outcome_labels = ['Cyclic (vs Sustained)', 'Discontinued (vs Sustained)']
        
        for i, outcome_label in enumerate(outcome_labels):
            print(f"\n--- DESFECHO: {outcome_label} ---")
            print(f"{ 'Variável':<40} | {'aOR':<6} | {'IC 95%':<18} | {'P-valor':<8}")
            print("-" * 80)
            
            eq_key = str(i + 1)

            for var_name in params.index:
                if "Intercept" in var_name or "Year" in var_name or "Region" in var_name: continue
                
                aor = params.iloc[params.index.get_loc(var_name), i]
                pval = pvalues.iloc[pvalues.index.get_loc(var_name), i]
                
                try:
                    c_low = conf.loc[(eq_key, var_name)][0]
                    c_high = conf.loc[(eq_key, var_name)][1]
                except KeyError:
                    c_low, c_high = 0, 0
                
                display_name = var_name[:38]
                display_name = display_name.replace("C(Pop, Treatment('HSH'))[T.", "Pop: ")
                display_name = display_name.replace("C(Edu, Treatment('High'))[T.", "Edu: ")
                display_name = display_name.replace("C(Race, Treatment('White'))[T.", "Race: ")
                display_name = display_name.replace("C(Age, Treatment('30-39'))[T.", "Age: ")
                display_name = display_name.replace("]", "")
                
                sig = "*" if pval < 0.05 else ""
                print(f"{display_name:<40} | {aor:.2f}   | {c_low:.2f} - {c_high:.2f}      | {pval:.3f} {sig}")
                
                results_list.append({
                    'Outcome': outcome_label,
                    'Variable_Raw': var_name,
                    'Variable_Clean': display_name.strip(),
                    'aOR': round(aor, 3),
                    'CI_Lower': round(c_low, 3),
                    'CI_Upper': round(c_high, 3),
                    'p_value': round(pval, 4),
                    'Significant': sig
                })

    except Exception as e:
        print(f"Erro regressão: {e}")
        return None
        
    return pd.DataFrame(results_list)

def main():
    print("--- ANÁLISE ROBUSTA DE PREP: PERFIS E REGRESSÃO MULTINOMIAL ---")
    DATA_FECHAMENTO = '2025-12-31' 
    
    # 1. Carregar
    try:
        bases = carregar_bases(pd.to_datetime(DATA_FECHAMENTO).date(), use_cache=True)
        df_disp = bases.get("Disp", pd.DataFrame())
        df_cad_prep = bases.get("Cadastro_PrEP", pd.DataFrame())
    except Exception as e:
        print(f"Erro: {e}")
        return

    # 2. Limpeza
    df_disp, df_disp_semdupl = clean_disp_df(df_disp, DATA_FECHAMENTO)
    df_cad_prep = process_cadastro(df_cad_prep)
    
    print("Aplicando enriquecimento e preprocessamento...")
    df_disp_semdupl = enrich_disp_data(df_disp_semdupl, df_cad_prep, pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
    try:
        df_cad_prep = calculate_population_groups(df_cad_prep)
    except: pass

    # 3. Classificação
    df_classificacao = classificar_comportamento(df_disp_semdupl, DATA_FECHAMENTO)
    
    # 4. Merge
    df_final = df_classificacao.merge(df_cad_prep, on='codigo_pac_eleito', how='left')
    
    # Calcular Faixa Etaria
    hoje = pd.to_datetime(DATA_FECHAMENTO)
    if 'data_nascimento' in df_final.columns:
        df_final['data_nascimento'] = pd.to_datetime(df_final['data_nascimento'], errors='coerce')
        df_final['idade'] = (hoje - df_final['data_nascimento']) / pd.to_timedelta(365.25, unit='D')
        bins = [0, 18, 24, 29, 39, 49, 100]
        labels = ['<18', '18-24', '25-29', '30-39', '40-49', '50+']
        df_final['faixa_etaria'] = pd.cut(df_final['idade'], bins=bins, labels=labels)
    
    # 5. Descritiva Simples
    print("\n>>> PERFIL (%) POR POPULAÇÃO <<<")
    ct = pd.crosstab(df_final['Pop_genero_pratica'], df_final['perfil_uso'], normalize='index') * 100
    print(ct.round(1).sort_values('Sustained', ascending=False).to_string())

    # --- ANÁLISE INTERSECCIONAL (Intersectional) ---
    print("\n" + "="*60)
    print("ANÁLISE INTERSECCIONAL (DETALHAMENTO)")
    print("="*60)
    
    # Lista para salvar no Excel
    intersectional_data = {}
    
    # População x Raça
    print("\n>>> Interseccionalidade: População x Raça/Cor")
    ct_race = pd.crosstab([df_final['Pop_genero_pratica'], df_final['raca4_cat']], df_final['perfil_uso'], normalize='index') * 100
    intersectional_data['Pop_Raca'] = ct_race
    
    # Tentar mostrar Travestis especificamente
    try:
        print("\nRecorte: TRAVESTIS por Raça/Cor:")
        print(ct_race.loc['Travestis'].round(1).to_string())
    except KeyError:
        pass
        
    # População x Escolaridade
    ct_edu = pd.crosstab([df_final['Pop_genero_pratica'], df_final['escol4']], df_final['perfil_uso'], normalize='index') * 100
    intersectional_data['Pop_Escolaridade'] = ct_edu
    
    try:
        print("\nRecorte: TRAVESTIS por Escolaridade:")
        print(ct_edu.loc['Travestis'].round(1).to_string())
    except KeyError:
        pass

    # População x Faixa Etária
    ct_age = pd.crosstab([df_final['Pop_genero_pratica'], df_final['faixa_etaria']], df_final['perfil_uso'], normalize='index') * 100
    intersectional_data['Pop_Idade'] = ct_age

    # 6. Regressão
    df_reg_results = executar_regressao_multinomial(df_final)
    
    # 7. Salvar Excel
    output_file = "Tabelas_Abstract_PrEP.xlsx"
    print(f"\nSalvando resultados em: {output_file}...")
    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            ct.round(1).to_excel(writer, sheet_name='Geral_Populacao')
            
            # Abas Interseccionais
            ct_race.round(1).to_excel(writer, sheet_name='Intersec_Pop_Raca')
            ct_edu.round(1).to_excel(writer, sheet_name='Intersec_Pop_Edu')
            ct_age.round(1).to_excel(writer, sheet_name='Intersec_Pop_Idade')
            
            if df_reg_results is not None:
                df_reg_results.to_excel(writer, sheet_name='Regressao_Multinomial', index=False)
        print("Arquivo Excel gerado com sucesso!")
    except Exception as e:
        print(f"Erro ao salvar Excel: {e}")

if __name__ == "__main__":
    main()