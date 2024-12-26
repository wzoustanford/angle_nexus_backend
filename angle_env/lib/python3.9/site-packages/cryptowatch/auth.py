import os
import yaml
import traceback

from cryptowatch.utils import log
from cryptowatch import errors


def read_config():
    user_home_dir = os.environ.get("HOME")
    filepath = "{}/.cw/credentials.yml".format(user_home_dir)
    api_key = None
    rest_url = None
    stream_url = None
    try:
        with open(filepath, "r") as config_file:
            config = yaml.safe_load(config_file)
            # A config_file empty or with all lines commented out will return None
            if not config:
                log("Your configuration file at {} is empty".format(filepath), is_debug=True)
            else:
                # Look for the (public) API Key
                if not config.get("apikey") and not config.get("api_key"):
                    log("No API key seen in credential file", is_debug=True)
                else:
                    api_key = config.get("apikey")
                    if api_key is None:
                        api_key = config.get("api_key")
                # Look for a stream (websocket) URL
                if not config.get("stream_url"):
                    log("No stream URL seen in credential file", is_debug=True)
                else:
                    stream_url = config.get("stream_url")
                # Look for a REST API URL
                if not config.get("rest_url"):
                    log("No rest URL seen in credential file", is_debug=True)
                else:
                    rest_url = config.get("rest_url")
    except FileNotFoundError as ex:
        log("No credential file found", is_debug=True)
    except yaml.YAMLError as ex:
        log("Credential is not a valid YAML file", is_error=True)
        raise error.CredentialsFileError(
            "Your Cryptowatch credentials file at "
            "{} is not properly formatted.".format(filepath)
        )
    except Exception as ex:
        log(traceback.format_exc(), is_error=True)
    finally:
        return api_key, rest_url, stream_url
