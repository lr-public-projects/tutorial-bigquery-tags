'''Módulo para interações com a API do BigQuery.'''

import logging
from typing import List, Dict, Any, Optional, Set

from google.cloud import bigquery


bq_client: bigquery.Client = bigquery.Client()

def sync_bigquery_column_policy_tags(
    full_table_id: str,
    tag_changes: Dict[str, Dict[str, List[Dict[str, str]]]]
) -> None:
    """
    Sincroniza as policy tags para colunas em uma tabela do BigQuery.

    Args:
        full_table_id (str): The full BigQuery table ID (e.g., 'project.dataset.table').
        tag_changes (Dict[str, Dict[str, List[Dict[str, str]]]]): 
            Um dicionário onde as chaves são nomes de colunas e os valores são
            dicionários contendo as ações ('add' ou 'remove') a serem aplicadas.
            Example:
            {
                "column_a": {
                    'changes': [
                        {'action': 'add', 'tag_name': 'projects/.../tag_id_to_add'},
                        {'action': 'remove', 'tag_name': 'projects/.../tag_id_to_remove'}
                    ]
                }
            }
    """
    logging.info('Starting sync for table: %s', full_table_id)
    try:
        # Get the current table to modify its schema
        bq_table: bigquery.Table = bq_client.get_table(full_table_id)
        new_schema: List[bigquery.SchemaField] = []

        for field in bq_table.schema:
            field: bigquery.SchemaField # Explicit type hint for clarity
            if field.name in tag_changes:
                logging.info('Processing column "%s" for policy tag changes.', field.name)
                tags: List[str] = list(field.policy_tags.names) if field.policy_tags else []
                for change_item in tag_changes[field.name]['changes']:
                    action: str = change_item['action']
                    tag_name: str = change_item['tag_name']

                    if action == 'add':
                        if tag_name not in tags:
                            tags.append(tag_name)
                            logging.info(
                                'Action: ADD policy tag "%s" to column "%s"',
                                tag_name, field.name
                            )
                        else:
                            logging.info(
                                'Policy tag "%s" already exists on column "%s". Skipping add.',
                                tag_name, field.name
                            )
                    elif action == 'remove':
                        if tag_name in tags:
                            tags.remove(tag_name)
                            logging.info(
                                'Action: REMOVE policy tag "%s" from column "%s"',
                                tag_name, field.name
                            )
                        else:
                            logging.warning(
                                'Warning: Attempted to remove non-existent tag "%s" from column "%s". Skipping remove.',
                                tag_name, field.name
                            )
                    else:
                        logging.warning(
                            'Warning: Unknown action "%s" for tag "%s" on column "%s". Skipping.',
                            action, tag_name, field.name
                        )

                # Cria um novo SchemaField com as policy tags atualizadas.
                # É importante criar um novo objeto PolicyTagList.
                updated_policy_tags: Optional[bigquery.PolicyTagList]
                if tags:
                    updated_policy_tags = bigquery.PolicyTagList(tags)
                else:
                    updated_policy_tags = None

                new_field: bigquery.SchemaField = bigquery.SchemaField(
                    name=field.name,
                    field_type=field.field_type,
                    mode=field.mode,
                    description=field.description,
                    policy_tags=updated_policy_tags, # Assign the updated policy tags
                    fields=field.fields # Preserve nested fields if any
                )
                new_schema.append(new_field)
            else:
                new_schema.append(field)

        # Atualiza a tabela. O field_mask 'schema' garante que apenas o schema seja modificado.
        updated_table: bigquery.Table = bigquery.Table(full_table_id, schema=new_schema)
        updated_table = bq_client.update_table(updated_table, ['schema'])
        logging.info('Successfully synced policy tags for table: %s', full_table_id)
    except Exception as e:
        logging.error('Error syncing policy tags for table %s: %s', full_table_id, e, exc_info=True)
        raise # Re-raise the exception after logging

def compare_policy_tag_lists(desired_tags: List[str], current_tags: List[str]) -> Dict[str, Any]:
    """
    Compara duas listas de policy tags e identifica as diferenças,
    gerando uma lista de ações para sincronizar o BigQuery com o estado desejado.

    Args:
        desired_tags (list[str]): A list of policy tag resource names as defined
                                   in Dataform (the expected state).
        current_tags (list[str]): A list of policy tag resource names as currently
                                   applied in BigQuery (the actual state).

    Returns:
        Um dicionário contendo os resultados da comparação:
        - 'changes': Uma lista de ações ('add' ou 'remove') e o nome do recurso da tag.
        - 'match': Um booleano indicando se as duas listas são idênticas.
    """
    logging.debug('Comparing desired tags: %s with current tags: %s', desired_tags, current_tags)
    desired_tags_set: Set[str] = set(desired_tags)
    current_tags_set: Set[str] = set(current_tags)

    # Tags que estão no Dataform mas não no BigQuery (precisam ser adicionadas)
    to_add: List[str] = list(desired_tags_set - current_tags_set)

    # Tags que estão no BigQuery mas não no Dataform (precisam ser removidas)
    to_remove: List[str] = list(current_tags_set - desired_tags_set)

    tag_changes: List[Dict[str, str]] = []
    for tag in sorted(to_add):
        tag_changes.append({'action': 'add', 'tag_name': tag})
    for tag in sorted(to_remove):
        tag_changes.append({'action': 'remove', 'tag_name': tag})

    are_identical: bool = not tag_changes

    logging.debug('Comparison result - changes: %s, match: %s', tag_changes, are_identical)
    return {
        'changes': tag_changes,
        'match': are_identical
    }

def get_bigquery_table_config(full_table_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Obtém a configuração atual de uma tabela do BigQuery, focando nos
    nomes das colunas e suas policy tags associadas.

    Args:
        full_table_id (str): The full BigQuery table ID (e.g., 'project.dataset.table').

    Returns:
        Um dicionário onde as chaves são nomes de colunas e os valores são dicionários contendo:
            - 'name': The column name.
            - 'policy_tags': A list of policy tag resource names applied to the column (if any).
                Example: 'projects/PROJECT_ID/.../POLICY_TAG_ID'
            Returns an empty dictionary if the table has no schema.
    """
    logging.info('Retrieving configuration for table: %s', full_table_id)
    table_config: Dict[str, Dict[str, Any]] = {}
    try:
        bq_table: bigquery.Table = bq_client.get_table(full_table_id)

        if bq_table.schema:
            for field in bq_table.schema:
                field: bigquery.SchemaField # Explicit type hint
                column_definition: Dict[str, Any] = {
                    'name': field.name,
                    'policy_tags': list(field.policy_tags.names) if field.policy_tags else []
                }
                table_config[field.name] = column_definition
        else:
            logging.warning('Warning: Table %s has no defined schema. Returning empty config.', full_table_id)

        logging.info('Successfully retrieved configuration for table: %s', full_table_id)
    except Exception as e:
        logging.error('Error retrieving configuration for table %s: %s', full_table_id, e, exc_info=True)
        raise
    return table_config
