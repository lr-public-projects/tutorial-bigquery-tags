'''Módulo principal'''

import http
import functions_framework
import logging

from flask import Response, Request
from google.cloud import logging as cloud_logging

from .process import validate_and_apply


log_client = cloud_logging.Client()
log_client.setup_logging()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

@functions_framework.http
def bq_taxonomy(request:Request) -> Response:
    """
    Sincroniza as policy tags do BigQuery com base nas definições dos arquivos
    de declaração do Dataform. A função é acionada por HTTP e lê sua
    configuração a partir de variáveis de ambiente.

    Args:
        request (flask.Request): O objeto de requisição HTTP (não utiliza parâmetros).

    Returns:
        O objeto Response, com o HTTTP Code e uma mensagem adicional.
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    try:
        logging.info('Starting Dataform to BigQuery policy tag synchronization process.')
        validate_and_apply()
        logging.info('BigQuery policy tag synchronization process completed.')
        return Response('OK', status=http.HTTPStatus.OK)
    except Exception as e: #pylint: disable=W0718
        logging.error('Error during execution: %s', str(e), exc_info=True)
        return Response('ERROR', status=http.HTTPStatus.INTERNAL_SERVER_ERROR)
