# -*- coding: utf-8 -*-
import csv
import numpy as np
import pandas as pd
from dict_stops import *

path_subway_dictionary = '/home/cata/Documentos/Datois/Diccionario-EstacionesMetro.csv'
path_csv_sequences = '/home/cata/Documentos/sequences/'

# Función que carga las estaciones de metro
# en un diccionario
def load_metro_dictionary():
    dict_metro = {}
    with open(path_subway_dictionary,mode='r') as infile:
        reader = csv.reader(infile,delimiter=';')
        dict_metro = {rows[5]:rows[7] for rows in reader}
    return dict_metro


# Función que estandariza los valores de los paraderos de subida 
# y bajada
def update_vals(row,data = load_metro_dictionary()):
    if row.par_subida in data:
        row.par_subida = data[row.par_subida]
    if row.par_bajada in data:
        row.par_bajada = data[row.par_bajada]
    return row

# Función que estandariza los valores de los paraderos de subida 
# y bajada
def add_vals(row,latlong,paradero,data = dict_latlong_stops):
    stop_name = row[paradero]
    if stop_name in data:
        return data[stop_name][latlong]
    else :
        return np.nan

# Función que busca los indices de los valores en la matriz que 
# coinciden con argumento
def quienCalzaCon(iden_matris,argumento):
    i = 0
    identified_indexs = []
    limit = len(iden_matris)
    while (i<limit):
        the_index = np.argmax(iden_matrix[:,i])
        if(the_index==argumento):
            identified_indexs.append(i)
        i += 1
    return identified_indexs
    

# Función que filtra un data_frame según id
# y el resultado lo entrega en un archivo csv
def queryToCSV(matrix, user_id, user_index, str_diff = ''):
    query = 'id ==' + str(user_id)
    df_query = matrix.query(query)
    file_path = path_csv_sequences + str(user_id) + '_' + str(user_index) + '_' + str_diff + '.csv'
    df_query.to_csv(path_or_buf=file_path)


# Función que configura el data frame con los datos
def frame_config(frame):
    frame['tiempo_subida'] = pd.to_datetime(frame.tiempo_subida)
    frame['weekday'] = frame.tiempo_subida.dt.dayofweek
    frame['lat_subida'] = frame.apply(add_vals,args=('lat','par_subida'),axis=1)
    frame['lat_bajada'] = frame.apply(add_vals,args=('lat','par_subida'),axis=1)
    frame['long_subida'] = frame.apply(add_vals,args=('long','par_subida'),axis=1)
    frame['long_bajada'] = frame.apply(add_vals,args=('long','par_bajada'),axis=1)
    frame = frame.sort_values(by=['id', 'tiempo_subida'])
    frame['diferencia_tiempo'] = (frame['tiempo_subida']-frame['tiempo_subida'].shift()).fillna(0)
    return frame.apply(update_vals, axis=1)


def hour_to_seconds(an_hour):
    return int(an_hour.hour*3600 + an_hour.minute *60 + an_hour.second)

def seconds_to_hour(a_lot_of_seconds):
    hour = int(a_lot_of_seconds/3600)
    minute = int((a_lot_of_seconds - hour * 3600)/60)
    second = a_lot_of_seconds - hour * 3600 - minute * 60
    return str(hour)+":"+str(minute)+":"+str(second) 