# -*- coding: utf-8 -*-
#Edit distance identification
import time
import datetime as dt
import pickle
import numpy as np
import random
import scipy as sp
from dict_stops import *
import pandas as pd
import os
import csv

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

def cost(a_tuple):
	return a_tuple

def delete(sequence,i,c):
	n = len(sequence)
	sum_lat = 0
	sum_long = 0
	sum_temp = 0
	for seq in sequence:
		sum_lat += seq[0]
		sum_long += seq[1]
		sum_temp += seq[2]
	lat_distance = (sum_lat/n-(sum_lat-sequence[i][0])/(n-1))**2
	long_distance = (sum_long/n-(sum_long-sequence[i][1])/(n-1))**2
	temporal_distance = (sum_temp/n-(sum_temp-sequence[i][2])/(n-1))**2
	spatial_distance = lat_distance + long_distance
	return ((1-c)*spatial_distance+c*temporal_distance)**0.5

def insert(sequence,pi,c):
	n = len(sequence)
	sum_lat = 0
	sum_long = 0
	sum_temp = 0
	for seq in sequence:
		sum_lat += seq[0]
		sum_long += seq[1]
		sum_temp += seq[2]
	lat_distance = (sum_lat/n-(sum_lat+(n*pi[0]))/(n+1))**2
	long_distance = (sum_long/n-(sum_long+(n*pi[0]))/(n+1))**2
	temporal_distance = (sum_temp/n-(sum_temp+(n*pi[0]))/(n+1))**2
	spatial_distance = lat_distance + long_distance
	return ((1-c)*spatial_distance+c*temporal_distance)**0.5
	 
def replace(sequence,pi,pj,c):
	n = len(sequence)
	sum_lat = 0
	sum_long = 0
	sum_temp = 0
	sum_lat_plus_pj = 0
	sum_long_plus_pj = 0
	sum_temp_plus_pj = 0
	for seq in sequence:
		sum_lat += seq[0]
		sum_long += seq[1]
		sum_temp += seq[2]
		sum_lat_plus_pj += seq[0] +pj[0]
		sum_long_plus_pj += seq[1] +pj[1]
		sum_temp_plus_pj += seq[2] +pj[2]
	sum_lat_plus_pj -= pi[0] +pj[0]
	sum_long_plus_pj -= pi[1] +pj[1]
	sum_temp_plus_pj -= pi[2] +pj[2]
	lat_distance = (sum_lat/n-(sum_lat+sum_lat_plus_pj)/n)/n**2
	long_distance = (sum_long/n-(sum_long+sum_long_plus_pj)/n)**2
	temporal_distance = (sum_temp/n-(sum_temp+sum_temp_plus_pj)/n)**2
	spatial_distance = lat_distance + long_distance
	return ((1-c)*spatial_distance+c*temporal_distance)**0.5

#sequence_a: S(s1,....sn)
#sequence_b: T(t1,....tn)
def get_edit_distance(sequence_a,sequence_b,i,j,c):
	#3 casos
    if len(sequence_a) == 0:
        return 0
    if i>=j:
        return 0
	#s_i deleted and s1,.....,s_i-1 is transformed to t1,....,tj
	d1 = get_edit_distance(sequence_a[0:len(sequence_a)-1],sequence_b,i-1,j,c) + cost(delete(sequence_a,i,c))
	#s1,....si is transformed into t1,....,t_j-1 and we insert t_j at the end
	d2 = get_edit_distance(sequence_a,sequence_b,i,j-1,c) + cost(insert(sequence_b[0:len(sequence_b)-1],sequence_b[j],c))
	#s_i is changed into tj and the rest s1,....,s_i-1 is transformed to t1,....,t_j-1
	d3 = get_edit_distance(sequence_a[0:len(sequence_a)-1].append(sequence_b[j]),sequence_b,i-1,j-1,c) + cost(replace(sequence_a,sequence_b,sequence_a[i],sequence_b[j],c))
    
    assert type(d1)==float and type(d2)==float and type(d3)==float
    return min(d1,d2,d3)

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

def frame_config(frame):
    frame['tiempo_subida'] = pd.to_datetime(frame.tiempo_subida)
    frame['tiempo_bajada'] = pd.to_datetime(frame.tiempo_bajada)
    frame = frame.apply(update_vals, axis=1)
    frame['weekday'] = frame.tiempo_subida.dt.dayofweek
    frame['lat_subida'] = frame.apply(add_vals,args=('lat','par_subida'),axis=1)
    frame['lat_bajada'] = frame.apply(add_vals,args=('lat','par_bajada'),axis=1)
    frame['long_subida'] = frame.apply(add_vals,args=('long','par_subida'),axis=1)
    frame['long_bajada'] = frame.apply(add_vals,args=('long','par_bajada'),axis=1)
    frame = frame.sort_values(by=['id', 'tiempo_subida'])
    frame['diferencia_tiempo'] = (frame['tiempo_subida']-frame['tiempo_subida'].shift()).fillna(0)
    return frame

def hour_to_seconds(an_hour):
    return int(an_hour.hour*3600 + an_hour.minute *60 + an_hour.second)

def buscar_locacion(mls,location):
	try:
		index_location = mls.index(location)
	except ValueError:
		index_location = -1
	return index_location

def create_sequence(id_user, mls, nvisitas, sequence):
	profile = {'user_id':id_user,'mls':mls,'nvisitas':nvisitas,'sequence':sequence}
	return profile

def get_sequences(ids,lat_subidas,long_subidas,t_subidas,lat_bajadas,long_bajadas,t_bajadas):
    # se inicializan las variables con los valores de la primera transaccion
    profiles= [] # arreglo de diccionarios
    First = True
    # inicializo para despues usarlas
    last_id = -22
    mls = []
    nvisitas = []
    sequence = []
    times = []
    counter = 0
    for transaction in zip(ids,lat_subidas,long_subidas,t_subidas,lat_bajadas,long_bajadas,t_bajadas):
        id_user = transaction[0]
        lat_subida = transaction[1]
        long_subida = transaction[2]
        t_subida = transaction[3]
        lat_bajada = transaction[4]
        long_bajada = transaction[5]
        t_bajada = transaction[6]
        counter += 1
        if (lat_subida!=lat_subida or t_subida != t_subida):
            continue 
        par_subida = (lat_subida,long_subida)
        par_bajada = (lat_bajada,long_bajada)
        subida_3 = (lat_subida,long_subida,hour_to_seconds(t_subida))
        if First:
            last_id = id_user
            mls = [par_subida]
            sequence = [subida_3]
            last_stop = par_subida
            times.append(hour_to_seconds(t_subida))
            nvisitas = [0]
            counter = 1
            First = False
        if id_user!=last_id:       
            profiles.append(create_sequence(last_id,mls,nvisitas,sequence))
            last_id = id_user
            mls = [par_subida]
            sequence = [subida_3]
            last_stop = par_subida
            nvisitas = [0]
            counter = 1

        index_subida = buscar_locacion(mls,par_subida)
        # si la subida no había sido visitada se debe agregar al mls
        if (index_subida < 0):
            mls.append(par_subida)
            nvisitas.append(1)
            index_subida = len(mls) - 1
            sequence.append(subida_3)
            times.append(hour_to_seconds(t_subida))
            # si la bajada no se pudo calcular solo se considera la subida y se deja para calcular tpm en la proxima ronda 
            if (lat_bajada!=lat_bajada or t_bajada != t_bajada):
                last_stop = par_subida
                #print "Iteración n°: " + str(counter) + " , no se pudo estimar la bajada"
            else:
                bajada_3 = (lat_bajada,long_bajada,hour_to_seconds(t_bajada))
                last_stop = par_bajada
                sequence.append(bajada_3)
                times.append(hour_to_seconds(t_bajada))
                index_bajada = buscar_locacion(mls,par_bajada)
                # si la bajada no se había visitado antes, agregar bajada y sumar nvisitas 
                if (index_bajada < 0):
                    mls.append(par_bajada)
                    index_bajada = len(mls)-1
                    nvisitas.append(1)
                # sumar nvisita 
                else:
                    nvisitas[index_bajada] = nvisitas[index_bajada]+1
        else:
            nvisitas[index_subida] = nvisitas[index_subida]+1
            
            if(par_subida!=last_stop):
                sequence.append(subida_3)
                times.append(hour_to_seconds(t_subida))
            # subida estaba de antes y no hay bajada
            # REVISAR SI ESTO NO ES REDUNDANTE!
            if (lat_bajada!=lat_bajada or t_bajada!=t_bajada):
                last_stop = par_subida
            # hay subida y bajada
            else:
                bajada_3 = (lat_bajada,long_bajada,hour_to_seconds(t_bajada))
                sequence.append(bajada_3)
                times.append(hour_to_seconds(t_bajada))
                last_stop = par_bajada
                index_bajada = buscar_locacion(mls,par_bajada)
                # hay bajada pero no estaba antes
                if (index_bajada<0):
                    mls.append(par_bajada)
                    index_bajada = len(mls) - 1
                    nvisitas.append(1)
                # subida y bajada estaban de antes
                else:
                    nvisitas[index_bajada] = nvisitas[index_bajada]+1
    profiles.append(create_sequence(last_id,mls,nvisitas,sequence))

    return profiles

# Funcion que compara la similitud entre un perfil y una secuencia de transacciones
# Se normaliza el calculo según el largo de la secuencia
# get_simliarity: [[int]] [string] [string] int int-> int 
def get_similarity(sequence_a,sequence_b):
	length_sequence_a = len(sequence_a)
	length_sequence_b = len(sequence_b)
    D = np.zeros((length_sequence_a+1,length_sequence_b+1))
    for i in range(length_sequence_a):
	    D[i+1,0] = D[i,0] + delete(sequence_a,i,c)
	for j in range(length_sequence_b):
	    D[0,j+1] = D[0,j] + insert(sequence_a,sequence_b[j],c)
	for i in range(1,length_sequence_a+1):
	    for j in range(1,length_sequence_b+1):
	        m1 = D[i-1,j-1] + replace(sequence_a,sequence_a[i-1],sequence_b[j-1],c)
	        m2 = D[i-1,j] + delete(sequence_a,i-1,c)
	        m3 = D[i,j-1] + insert(sequence_a,sequence_b[j-1],c)
	        D[i,j] = min(m1,m2,m3)

    return D[length_sequence_a,length_sequence_b]

# Funcion que construye la matriz de identificacion en que cada indice corresponde
# a la similitud entre la i-esima tpm y la j-esima secuencia, obtenidas a partir de un
# perfil de usuario y un periodo de identificacion.
# len(users_profiles) == len(users_sequences)
# asume que los usuarios de users_profiles y users_sequences son los mismos
# get_identification_matrix; get_profiles(...) get_sequences(...) -> [[int]]
def get_identification_matrix(profiles):
	i = 0
	j = 0
	limit = len(profiles)
	identification_matrix = np.zeros((limit,limit))
	for profile_i in profiles:
		sequence_a = profile_i['sequence']
		j=0
		for profile_j in profiles:
			sequence_b = profile_j['sequence']
			identification_matrix[i,j] = get_similarity(sequence_a,sequence_b)
			j += 1
		i += 1
	return identification_matrix