# -*- coding: utf-8 -*-
import csv
import os
import numpy as np

if os.name == 'nt':
    path_subway_dictionary = 'C:\Users\catalina\Documents\Datois\Diccionario-EstacionesMetro.csv'
    path_csv_sequences = 'C:\Users\catalina\Documents\sequences\\'
else:
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
    frame = frame.sort_values(by=['id', 'tiempo_subida'])
    frame['diferencia_tiempo'] = (frame['tiempo_subida']-frame['tiempo_subida'].shift()).fillna(0)
    return frame.apply(update_vals, axis=1)


def get_n_correct_tpm(a_matrix,limit):
    identified_indexs = [] #almacena los indices de que secuencia fue seleccionada como match
    wrong_indexs = [] # almacena los indices de los que se clasificaron incorrectamente
    correct_indexs = [] # almacena los indices de los que se clasificaron correctamente
    correct_distance = []
    selected_distance = [] # almacena la distancia de los seleccionados
    abstenidos = []
    n_identified = 0
    wrong_distances = []
    for i in range(limit):
        the_index = np.argmax(a_matrix[:,i])
        if a_matrix[the_index,i] < -800:
            abstenidos.append(the_index)
            continue
        identified_indexs.append(the_index)
        selected_distance.append(a_matrix[the_index,i])
        distance = a_matrix[i,i]
        if(the_index!=i):
            wrong_indexs.append(i)
            wrong_distances.append(distance)
        else:
            correct_indexs.append(the_index)
            correct_distance.append(distance)
            n_identified += 1
    return [n_identified,selected_distance,identified_indexs,abstenidos,correct_indexs,correct_distance,wrong_indexs,wrong_distances]