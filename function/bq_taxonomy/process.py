'''Módulo principal para o processo de validação e aplicação das tags'''

import os
import re
import logging

from collections import namedtuple # type: ignore
from typing import List, Dict, Any

from . import dataform as df
from . import bigquery as bq

PROJECT_ID: str = os.environ['PROJECT_ID']
REGION_ID: str = os.environ.get('REGION_ID', 'us-central1')
REPOSITORY_ID: str = os.environ['REPOSITORY_ID']
WORKSPACE_ID: str = os.environ['WORKSPACE_ID']
BASE_FOLDER: str = os.environ['BASE_FOLDER']

File = namedtuple('File', ['full_file_name', 'full_table_id', 'definition'])

def validate_and_apply() -> None:
    """
    Orquestra o processo de ponta a ponta para sincronizar as policy tags
    dos arquivos de declaração do Dataform com as tabelas do BigQuery.

    O processo envolve:
    1. Encontrar todos os arquivos dentro do `BASE_FOLDER` especificado no workspace do Dataform.
    2. Filtrar os arquivos do tipo 'declaration'.
    3. Para cada arquivo de declaração, analisar seu conteúdo para identificar a tabela
       de destino no BigQuery e as policy tags desejadas para cada coluna.
    4. Obter as policy tags atuais da tabela correspondente no BigQuery.
    5. Comparar o estado desejado (do Dataform) com o estado atual (do BigQuery).
    6. Aplicar quaisquer adições ou remoções de policy tags necessárias ao schema
       da tabela do BigQuery.
    """
    workspace: str = df.df_client.workspace_path(PROJECT_ID, REGION_ID, REPOSITORY_ID, WORKSPACE_ID)

    files: List[str] = []
    logging.info('Collecting Dataform files from "%s" directory.', BASE_FOLDER)
    # Pass workspace to get_files for recursive calls
    df.get_files(files, df.request_directory(workspace, BASE_FOLDER), workspace)
    logging.info('Found %d files in Dataform workspace.', len(files))

    declaration: str = r'type:\s\"declaration\"'
    usable_files: List[File] = []
    logging.info('Filtering for Dataform declaration files and extracting table information.')
    for f in files:
        file_content: str = df.read_file(workspace, f)

        if re.search(declaration, file_content):
            parsed_file: Dict[str, Any] = df.parse_file(file_content)
            assert 'schema' in parsed_file, f"File {f} is missing the 'schema' key."
            assert 'name' in parsed_file, f"File {f} is missing the 'name' key."

            # Construct the full table ID, using PROJECT_ID as a default for the database
            full_table: str = '{project}.{schema}.{name}'.format(
                project=parsed_file.get('database', PROJECT_ID),
                schema=parsed_file['schema'],
                name=parsed_file['name']
            )
            usable_files.append(File(f, full_table, parsed_file))
            logging.debug('Identified declaration file: %s -> BigQuery table: %s', f, full_table)
        else:
            logging.info('Skipping file %s: Not a declaration file.', f)

    if not usable_files:
        logging.info('No usable declaration files found. Exiting.')
        return

    logging.info('Identified %d usable declaration files.', len(usable_files))
    for t in usable_files:
        logging.info(
            'Processing BigQuery table: %s from Dataform file: %s',
            t.full_table_id, t.full_file_name
        )
        changes: Dict[str, Dict[str, List[Dict[str, str]]]] = {}
        table_bq_config: Dict[str, Dict[str, Any]] = bq.get_bigquery_table_config(t.full_table_id)

        assert 'columns' in t.definition, \
            f"Dataform definition for {t.full_table_id} is missing the 'columns' key."
        assert isinstance(t.definition['columns'], dict), \
            f"The 'columns' key for {t.full_table_id} is not a dictionary."
        for column_name, column_def in t.definition['columns'].items():
            # Ensure column exists in BQ config and has 'bigqueryPolicyTags' in Dataform definition
            if column_name in table_bq_config and 'bigqueryPolicyTags' in column_def:
                desired_tags: List[str] = column_def['bigqueryPolicyTags']
                current_tags: List[str] = table_bq_config[column_name]['policy_tags']
                diffs: Dict[str, Any] = bq.compare_policy_tag_lists(desired_tags, current_tags)
                if not diffs['match']:
                    changes[column_name] = diffs
                    logging.info(
                        'Changes detected for column "%s" in table "%s".',
                        column_name, t.full_table_id
                    )
                else:
                    logging.debug(
                        'No policy tag changes for column "%s" in table "%s".',
                        column_name, t.full_table_id
                    )
            elif column_name not in table_bq_config:
                logging.warning(
                    ('Column "%s" from Dataform definition not found in BigQuery table "%s".'
                    'Skipping policy tag comparison for this column.'),
                    column_name, t.full_table_id
                )
            # else: column_def might not have 'bigqueryPolicyTags', which is fine.

        if changes:
            logging.info(
                'Applying %d column policy tag changes to table: %s', len(changes),
                t.full_table_id
            )
            bq.sync_bigquery_column_policy_tags(t.full_table_id, changes)
        else:
            logging.info(
                'No policy tag changes needed for table: %s',
                t.full_table_id
            )
