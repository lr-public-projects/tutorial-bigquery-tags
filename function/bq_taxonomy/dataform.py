'''Módulo para interações com a API do Dataform.'''

import json
import re
import logging

from typing import Iterator, List, Dict, Any

from google.cloud import dataform


df_client: dataform.DataformClient = dataform.DataformClient()

def request_directory(workspace_name: str, path: str) -> Iterator[dataform.QueryDirectoryContentsResponse]:
    """
    Consulta o conteúdo de um diretório no Dataform.

    Args:
        workspace_name (str): The full resource name of the Dataform workspace.
        path (str): The path to the directory within the workspace.

    Returns:
        Iterator[dataform.QueryDirectoryContentsResponse]: An iterator over the
                                                           directory contents responses.
    """
    logging.debug('Requesting directory contents for workspace: %s, path: %s', workspace_name, path)
    try:
        query_directory: dataform.QueryDirectoryContentsRequest = dataform.QueryDirectoryContentsRequest(
            workspace=workspace_name, path=path
        )
        return df_client.query_directory_contents(query_directory).pages
    except Exception as e:
        logging.error('Error requesting directory contents for workspace %s, path %s: %s',
                      workspace_name, path, e, exc_info=True
        )
        raise

def parse_file(content: str) -> Dict[str, Any]:
    """
    Analisa o conteúdo de um arquivo de declaração do Dataform.
    Tenta converter o conteúdo em um formato compatível com JSON, adicionando
    aspas a chaves não citadas, e então o carrega como um dicionário Python.

    Args:
        content (str): The string content of the file to parse.

    Returns:
        Dict[str, Any]: The parsed content as a Python dictionary.

    Raises:
        json.JSONDecodeError: If the content cannot be parsed as valid JSON.
    """
    logging.debug('Attempting to parse file content (first 100 chars): %s...', content[:100])
    try:
        # Regex para encontrar chaves sem aspas seguidas por dois pontos.
        # Necessário porque os arquivos de declaração do Dataform usam uma sintaxe
        # semelhante a JavaScript, que não é JSON válido.
        # (\w+): Captura uma ou mais "word characters" (letras, números, underscore).
        # \s*: Corresponde a zero ou mais espaços em branco.
        # :    : Corresponde ao literal de dois pontos.
        pattern: str = r'(\w+)\s*:'

        start_index: int = content.find('{')
        if start_index == -1: # pragma: no cover
            raise ValueError('No JSON-like object found in content.')

        # Replace unquoted keys with double-quoted keys
        # We use r'"\1":' to replace the found word (\1) with itself surrounded by double quotes, plus the colon.
        json_compatible_string: str = re.sub(pattern, r'"\1":', content[start_index:])

        python_dict_regex: Dict[str, Any] = json.loads(json_compatible_string)
        logging.debug('Successfully parsed file content.')
        return python_dict_regex
    except json.JSONDecodeError as e:
        logging.error('JSON decoding error while parsing file content: %s', e, exc_info=True)
        raise
    except ValueError as e:
        logging.error('Value error while parsing file content: %s', e, exc_info=True)
        raise
    except Exception as e:
        logging.error('An unexpected error occurred during file parsing: %s', e, exc_info=True)
        raise

def get_files(
        list_file: List[str],
        pages: Iterator[dataform.QueryDirectoryContentsResponse],
        workspace_name: str
    ) -> None:
    """
    Percorre recursivamente os diretórios do Dataform para coletar todos os caminhos de arquivo.

    Args:
        list_file (List[str]): A list to append the full file paths to.
        pages (Iterator[dataform.QueryDirectoryContentsResponse]): An iterator over
                                                                   directory contents responses.
        workspace_name (str): The full resource name of the Dataform workspace,
                              needed for recursive calls to request_directory.
    """
    for p in pages:
        for e in p.directory_entries:
            if e.directory:
                logging.debug('Found directory: %s. Recursing...', e.directory)
                # Pass workspace_name to request_directory for recursive calls
                get_files(list_file, request_directory(workspace_name, e.directory), workspace_name)
            else:
                logging.debug('Found file: %s', e.file)
                list_file.append(e.file)

def read_file(workspace_name: str, file_path: str) -> str:
    """
    Lê o conteúdo de um arquivo de um workspace do Dataform.

    Args:
        workspace_name (str): O nome completo do recurso do workspace.
        file_path (str): O caminho para o arquivo dentro do workspace.

    Returns:
        str: O conteúdo do arquivo como uma string decodificada em UTF-8.
    """
    logging.debug('Reading file: %s from workspace: %s', file_path, workspace_name)
    try:
        cmd = dataform.ReadFileRequest(workspace=workspace_name, path=file_path)
        query_file = df_client.read_file(cmd)
        return query_file.file_contents.decode('utf-8')
    except Exception as e:
        logging.error('Error reading file %s from workspace %s: %s', file_path, workspace_name, e, exc_info=True)
        raise
