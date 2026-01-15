import logging
from pathlib import Path
from typing import Callable, Optional, Tuple, Set

logger = logging.getLogger(__name__)

class KeysExtractorLogic:
    """
    Lógica para extrair chaves de acesso (NFe/CTe) de um arquivo SPED.
    ATUALIZAÇÃO: Separação visual entre CTe (primeiro) e NFe (depois).
    FILTRO: Apenas ENTRADAS (Compras e Fretes tomados).
    """

    def __init__(self):
        logger.info("KeysExtractorLogic (Modo ENTRADAS - Separado por Tipo) inicializado.")

    def extract_keys(self, 
                     input_path: str, 
                     output_path: str, 
                     progress_callback: Optional[Callable[[int], None]] = None
                     ) -> Tuple[bool, str]:
        
        # CRIAÇÃO DE DOIS GRUPOS DISTINTOS
        nfe_keys: Set[str] = set()
        cte_keys: Set[str] = set()
        
        cnpj_declarante = "Desconhecido"
        lines_read = 0
        total_lines = 0
        
        try:
            input_p = Path(input_path)
            output_p = Path(output_path)

            if not input_p.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

            # 1. Contagem de linhas para a barra de progresso
            if progress_callback:
                try:
                    with open(input_p, 'r', encoding='latin-1', errors='ignore') as f:
                        total_lines = sum(1 for _ in f)
                except Exception:
                    total_lines = 0

            logger.info(f"Iniciando varredura organizada em: {input_p}")

            # 2. Leitura do arquivo
            with open(input_p, 'r', encoding='latin-1', errors='ignore') as infile:
                for line in infile:
                    lines_read += 1
                    
                    # Atualiza progresso a cada 5000 linhas
                    if progress_callback and total_lines > 0 and lines_read % 5000 == 0:
                        percent = int((lines_read / total_lines) * 100)
                        progress_callback(percent)

                    line = line.strip()
                    if not line.startswith('|') or not line.endswith('|'):
                        continue
                    
                    parts = line.split('|')
                    if len(parts) < 3: continue
                    
                    reg = parts[1]
                    
                    # Captura CNPJ Declarante (apenas informativo se precisar depois)
                    if reg == '0000' and len(parts) > 7:
                        cnpj_declarante = parts[7]

                    # --- TRATAMENTO ESPECÍFICO POR TIPO DE NOTA ---
                    
                    # C100: Nota Fiscal (NFe) -> Vai para nfe_keys
                    elif reg == 'C100':
                        if len(parts) > 9:
                            ind_oper = parts[2]
                            chave = parts[9]
                            
                            if ind_oper == '0': # 0 = Entrada
                                chave_limpa = ''.join(filter(str.isdigit, chave))
                                if len(chave_limpa) == 44:
                                    nfe_keys.add(chave_limpa)

                    # D100: Conhecimento de Transporte (CTe) -> Vai para cte_keys
                    elif reg == 'D100':
                        if len(parts) > 10:
                            ind_oper = parts[2]
                            chave = parts[10] # D100 é coluna 10
                            
                            if ind_oper == '0': # 0 = Entrada (Tomador)
                                chave_limpa = ''.join(filter(str.isdigit, chave))
                                if len(chave_limpa) == 44:
                                    cte_keys.add(chave_limpa)

            # 3. Salva o resultado de forma sequencial e organizada
            with open(output_p, 'w', encoding='utf-8') as outfile:
                
                # --- BLOCO 1: ESCREVE OS CTe PRIMEIRO ---
                if cte_keys:
                    outfile.write("=== LISTA DE CTe (Conhecimentos de Transporte) ===\n")
                    for key in sorted(cte_keys):
                        outfile.write(f"{key}\n")
                else:
                    outfile.write("=== NENHUM CTe ENCONTRADO ===\n")

                # --- SEPARADOR VISUAL ---
                outfile.write("\n\n") 
                outfile.write("==================================================\n")
                outfile.write("\n\n")

                # --- BLOCO 2: ESCREVE AS NFe DEPOIS ---
                if nfe_keys:
                    outfile.write("=== LISTA DE NFe (Notas Fiscais) ===\n")
                    for key in sorted(nfe_keys):
                        outfile.write(f"{key}\n")
                else:
                    outfile.write("=== NENHUMA NFe ENCONTRADA ===\n")

            if progress_callback: progress_callback(100)

            total_found = len(cte_keys) + len(nfe_keys)
            msg = (f"Extração concluída!\n\n"
                   f"CTe encontrados: {len(cte_keys)}\n"
                   f"NFe encontradas: {len(nfe_keys)}\n"
                   f"Total: {total_found}\n"
                   f"Arquivo gerado: {output_p.name}")
            
            logger.info(f"Sucesso. {total_found} chaves extraídas.")
            return True, msg

        except Exception as e:
            logger.error(f"Erro fatal: {e}", exc_info=True)
            return False, f"Erro: {str(e)}"