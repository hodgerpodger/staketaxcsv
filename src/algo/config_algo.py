from staketaxcsv.common import ExporterTypes as et
from staketaxcsv.common.config import config


class localconfig(config):

    start_date = None
    end_date = None
    lp_treatment = et.LP_TREATMENT_DEFAULT
    exclude_asas = []
    algofi_storage_address = None
