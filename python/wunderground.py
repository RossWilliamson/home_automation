import urllib2
import json


def collect_pws(pws="KCAALTAD10", 
                  key="c0464283a5ab0417"):

    """Collects weather data from personel station and
    returns info that is useful - default 

    Parameters
    ----------
    pws : string
        This is the personell weather station ID
    key : string
        This is my weather underground API key

    Returns
    -------
    w_data : dictionary
        Dictionary of extracted useful data

    Notes
    -----

    The Free API key only allows a connection 10 times per 
    minute and 500 calls a day. Seen as it will be on all
    the time don't call more than once every 5 minutes

    """
    url_str = "http://api.wunderground.com/api/%s/conditions/q/pws:%s.json" % (key, pws)

    f = urllib2.urlopen(url_str)
    json_string = f.read()
    parsed_json = json.loads(json_string)
    f.close()

    parsed_json = parsed_json['current_observation']
    w_data = {}
    w_data["temperature"] = parsed_json['temp_c']
    w_data["humidity"] = float(parsed_json['relative_humidity'][:-1])
    w_data["pressure"] = float(parsed_json['pressure_mb'])
    w_data["wind_dir"] = parsed_json['wind_degrees']
    w_data["wind_mph"] = parsed_json['wind_mph']
    w_data["precip_hour"] = float(parsed_json['precip_1hr_metric'])
    w_data["precip_day"] = float(parsed_json['precip_today_metric'])

    return w_data

