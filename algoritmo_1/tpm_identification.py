
# coding: utf-8
# modulo tpm_identification

# Este modulo contiene las funciones para extraer perfiles de movilidad
# a partir de un dataset de registros de transacciones en transporte publico.
# Los registros deben tener identificador del usuario, origen de la transacción 
# y destino.
# El perfil resultante de cada usuario corresponde a una matriz TPM (Transition 
# Probability Matrix), un arreglo mls (Minimum Location Set), el id del usuario, 
# y un arreglo del numero de visitas a cada ĺocacion del mls.


import numpy as np
import pandas as pd 
import time
import csv
import datetime


# Funcion que crea el diccionario perfil de usuario
# create_profile: string [string] [int] [[int]] ->{'user_id': string, 'mls':[int], 
#                                               'tpm':[[int]], 'nvisitas': int}
def create_profile(id_user, mls, nvisitas, tpm):
    n_locations = len(mls)
    tpm = tpm[0:n_locations,0:n_locations]
    tpm = tpm/tpm.sum(axis=1)[:,None]
    profile = {'user_id':id_user,'mls':mls,'tpm':tpm,'nvisitas':nvisitas}
    return profile

# Funcion que crea el diccionario perfil de usuario
# create_profile: string [string] [int] [[int]] ->{'user_id': string, 'mls':[int], 
#                                               'tpm':[[int]], 'nvisitas': int}
def create_spatiotemporal_profile(id_user, mls, nvisitas, tpm):
    n_locations = len(mls)
    tpm = tpm[0:n_locations*4,0:n_locations]
    tpm = tpm/tpm.sum(axis=1)[:,None]
    profile = {'user_id':id_user,'mls':mls,'tpm':tpm,'nvisitas':nvisitas}
    return profile

# Funcion que crea el diccionario perfil de usuario
# create_spatiotemporal_profile_2: string [string] [int] [[int]] ->{'user_id': string, 'mls':[int], 
#                                               'tpm':[[int]], 'nvisitas': int}
def create_spatiotemporal_profile_2(id_user, mls, nvisitas, tpm):
    n_locations = len(mls)
    tpm = np.asmatrix(tpm[0:n_locations*4,0:n_locations])
    profile = {'user_id':id_user,'mls':mls,'tpm':tpm,'nvisitas':nvisitas}
    return profile

# Funcion que busca una locacion en el arreglo mls y retorna el indice
# buscar_locacion: [string] string -> int
def buscar_locacion(mls,location):
    try:
        index_location = mls.index(location)
    except ValueError:
        index_location = -1
    return index_location

# Funcion que entrega los perfiles de usuario a partir de los registros 
# de transacciones. Utilizar con los registros del periodo de creacion de 
# perfiles.
# get_profiles: [string] [string] [string] -> [{'user_id': string, 'mls':[int], 
#                                               'tpm':[[int]], 'nvisitas': int}]
def get_profiles(ids, par_subidas, par_bajadas):
    # se inicializan las variables con los valores de la primera transaccion
    matrix_size = 30
    users_profiles= [] # arreglo de diccionarios
    First = True
    last_id = -1
    mls = []
    tpm = []
    nvisitas = []
    for transaction in zip(ids,par_subidas,par_bajadas):
        user_id = transaction[0]
        par_subida = transaction[1]
        par_bajada = transaction[2]
        # no se pierde el paradero de bajada, porque cuando no hay subida no se puede estimar la bajada
        if (par_subida!=par_subida):
            continue 
        if First:
            last_id = user_id
            tpm = np.zeros((matrix_size,matrix_size))
            mls = [par_subida]
            last_stop = par_subida
            last_stop_index = 0
            nvisitas = [0]
            First = False
        # guardar perfil y construir nueva TPM y mls no vacia para que no se caiga
        if user_id!=last_id:
            users_profiles.append(create_profile(last_id,mls,nvisitas,tpm))
            last_id = user_id
            tpm = np.zeros((matrix_size,matrix_size))
            mls = [par_subida]
            last_stop = par_subida
            last_stop_index = 0
            nvisitas = [0]

        index_subida = buscar_locacion(mls,par_subida)
        # si la subida no había sido visitada se debe agregar al mls
        if (index_subida < 0):
            if(len(mls)<matrix_size-1):
                mls.append(par_subida)
                nvisitas.append(1)
                index_subida = len(mls) - 1
                if(par_subida!=last_stop):
                    tpm[last_stop_index,index_subida] +=1
                # si la bajada no se pudo calcular solo se considera la subida y 
                # se deja para calcular tpm en la proxima ronda 
                if (par_bajada!=par_bajada):
                    last_stop = par_subida
                    last_stop_index = index_subida
                else:
                    index_bajada = buscar_locacion(mls,par_bajada)
                    # si la bajada no se había visitado antes, agregar bajada y sumar nvisitas 
                    if (index_bajada < 0):
                        mls.append(par_bajada)
                        nvisitas.append(1)
                        index_bajada = len(mls) - 1
                        tpm[index_subida,index_bajada] +=1
                    # sumar nvisita 
                    else:
                        if(index_subida!=index_bajada):
                            nvisitas[index_bajada] = nvisitas[index_bajada]+1
                            tpm[index_subida,index_bajada] +=1
                    last_stop = par_bajada
                    last_stop_index = index_bajada
        else:
            nvisitas[index_subida] = nvisitas[index_subida]+1
            if(par_subida!=last_stop):
                    tpm[last_stop_index,index_subida] +=1
            # subida estaba de antes y no hay bajada
            # REVISAR SI ESTO NO ES REDUNDANTE!
            if (par_bajada!=par_bajada):
                last_stop = par_subida
                last_stop_index = index_subida
            # hay subida y bajada
            else:
                index_bajada = buscar_locacion(mls,par_bajada)
                # hay bajada pero no estaba antes
                if (index_bajada<0):
                    if(len(mls)<matrix_size-1):
                        mls.append(par_bajada)
                        last_stop = par_bajada
                        nvisitas.append(1)
                        index_bajada = len(mls) - 1
                        last_stop_index = index_bajada
                        tpm[index_subida,index_bajada] +=1
                    else:
                        last_stop = par_subida
                        last_stop_index = index_subida
                # subida y bajada estaban de antes
                else:
                    if(index_bajada!=index_subida):
                        nvisitas[index_bajada] = nvisitas[index_bajada]+1
                        tpm[index_subida,index_bajada] +=1
                        last_stop = par_bajada
                        last_stop_index = index_bajada
    #agrego el ultimo perfil
    users_profiles.append(create_profile(last_id,mls,nvisitas,tpm))

    return users_profiles

# Funcion que crea el diccionario con los datos de la secuencia
# create_sequence: string [string] [int] [string] ->{'user_id': string, 'mls':[int], 
#                                               'nvisitas': int, 'sequence': [string]}
def create_sequence(id_user, mls, nvisitas, sequence,timestamps=None):
    if timestamps == None:
        profile = {'user_id':id_user,'mls':mls,'nvisitas':nvisitas,'sequence':sequence}
    else:
        profile = {'user_id':id_user,'mls':mls,'nvisitas':nvisitas,'sequence':sequence,'timestamps':timestamps} 
    return profile

# Funcion que entrega las secuencias de usuario a partir de los registros de 
# transacciones. Utilizar con los registros del periodo de identificacion.
# get_sequences: [string] [string] [string] -> [{'user_id': string, 'mls':[int], 
#                                               'sequence':[string], 'nvisitas': int}]
def get_sequences(ids, par_subidas, par_bajadas):
    # se inicializan las variables con los valores de la primera transaccion
    profiles= [] # arreglo de diccionarios
    First = True
    # inicializo para despues usarlas
    last_id = -22
    mls = []
    nvisitas = []
    sequence = []
    for transaction in zip(ids,par_subidas,par_bajadas):
        id_user = transaction[0]
        par_subida = transaction[1]
        par_bajada = transaction[2]
        if (par_subida!=par_subida):
            continue 
        if First:
            last_id = id_user
            mls = [par_subida]
            sequence = [par_subida]
            last_stop = par_subida
            nvisitas = [0]
            counter = 1
            First = False
        if id_user!=last_id:       
            profiles.append(create_sequence(last_id,mls,nvisitas,sequence))
            last_id = id_user
            mls = [par_subida]
            sequence = [par_subida]
            last_stop = par_subida
            nvisitas = [0]
            counter = 1
            
        index_subida = buscar_locacion(mls,par_subida)
        # si la subida no había sido visitada se debe agregar al mls
        if (index_subida < 0):
            mls.append(par_subida)
            nvisitas.append(1)
            index_subida = len(mls) - 1
            sequence.append(par_subida)
            # si la bajada no se pudo calcular solo se considera la subida y se deja para calcular tpm en la proxima ronda 
            if (par_bajada!=par_bajada):
                last_stop = par_subida
                #print "Iteración n°: " + str(counter) + " , no se pudo estimar la bajada"
            else:
                last_stop = par_bajada
                sequence.append(par_bajada)
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
                sequence.append(par_subida)
            # subida estaba de antes y no hay bajada
            # REVISAR SI ESTO NO ES REDUNDANTE!
            if (par_bajada!=par_bajada):
                last_stop = par_subida
            # hay subida y bajada
            else:
                sequence.append(par_bajada)
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
def get_similarity(tpm,mls,sequence,expzero=-800,expnan=-800):
    similarity = 0
    travel_counter = 0
    length_sequence = len(sequence)
    p_zero = pow(10,expzero/length_sequence)
    p_nan = pow(10, expnan/length_sequence)
    index_subida = buscar_locacion(mls,sequence[0])
    for travel in sequence[1:]:
        # buscar pik en tpm
        index_bajada = buscar_locacion(mls,travel)
        if(index_bajada < 0 or index_subida < 0):
            pik = p_nan
        else:
            pik = tpm[index_subida, index_bajada]
        if(pik != pik):
            pik = p_nan
        elif(pik == 0):
            pik = p_zero
        # sumar log10
        similarity += np.log10(pik)
        index_subida = index_bajada

    return similarity

# Funcion que compara la similitud entre un perfil y una secuencia de transacciones
# Se normaliza el calculo según el largo de la secuencia
# get_simliarity: [[int]] [string] [string] int int-> int 
def get_spatiotemporal_similarity(tpm,mls,sequence,timestamps,expzero=-800,expnan=-800):
    similarity = 0
    travel_counter = 0
    length_sequence = len(sequence)
    p_zero = pow(10,expzero/length_sequence)
    p_nan = pow(10, expnan/length_sequence)
    index_subida = buscar_locacion(mls,sequence[0])
    for travel in sequence[1:]:
        horario = get_horario(timestamps[travel_counter].time())
        # buscar pik en tpm
        index_bajada = buscar_locacion(mls,travel)
        if(index_bajada < 0 or index_subida < 0):
            pik = p_nan
        else:
            pik = tpm[(index_subida*4)+horario, index_bajada]
        if(pik != pik):
            pik = p_nan
        elif(pik == 0):
            pik = p_zero
        # sumar log10
        similarity += np.log10(pik)
        index_subida = index_bajada
        travel_counter += 1
    return similarity


def get_pik_base(tpm,index_subida,index_bajada):
    tpm_original = tpm[index_subida:index_subida+3,:].sum(axis=0)
    row_total = tpm_original.sum(axis=1)[0,0]
    total_index_subida = tpm[index_subida:index_subida+3,index_bajada].sum(axis=0)[0,0]
    return total_index_subida/row_total

#porcentaje en relacion a las casilla index_subida index_bajada
def get_pik_bonus(tpm,index_subida,index_bajada,horario):
    total_cells_subida_bajada = tpm[index_subida:index_subida+3,index_bajada].sum(axis=0)[0,0]
    return tpm[index_subida+horario,index_bajada]/total_cells_subida_bajada

def get_pik_bonus_2(tpm,index_subida,index_bajada,horario):
    tpm_original = tpm[index_subida:index_subida+3,:].sum(axis=0)
    row_total = tpm_original.sum(axis=1)[0,0]
    return tpm[index_subida+horario,index_bajada]/row_total

# Funcion que compara la similitud entre un perfil y una secuencia de transacciones
# Se normaliza el calculo según el largo de la secuencia
# la tpm no viene probabilidades
# get_simliarity: [[int]] [string] [string] int int-> int 
def get_spatiotemporal_similarity_2(tpm,mls,sequence,timestamps,expzero=-800,expnan=-800):
    similarity = 0
    travel_counter = 0
    length_sequence = len(sequence)
    p_zero = pow(10,expzero/length_sequence)
    p_nan = pow(10, expnan/length_sequence)
    index_subida = buscar_locacion(mls,sequence[0])
    for travel in sequence[1:]:
        horario = get_horario(timestamps[travel_counter].time())
        # buscar pik en tpm
        index_bajada = buscar_locacion(mls,travel)
        if(index_bajada < 0 or index_subida < 0):
            pik = p_nan
        else:
            pik_base = get_pik_base(tpm,index_subida,index_bajada)
            pik_bonus = get_pik_bonus(tpm,index_subida,index_bajada,horario)
            pik = pik_base + pik_bonus
        if pik != pik:
            pik = p_nan
        elif(pik == 0):
            pik = p_zero
        # sumar log10
        similarity += np.log10(pik)
        index_subida = index_bajada
        travel_counter += 1
    return similarity

# Funcion que compara la similitud entre un perfil y una secuencia de transacciones
# Se normaliza el calculo según el largo de la secuencia
# la tpm no viene probabilidades
# get_simliarity: [[int]] [string] [string] int int-> int 
def get_spatiotemporal_similarity_3(tpm,mls,sequence,timestamps,expzero=-800,expnan=-800):
    similarity = 0
    travel_counter = 0
    length_sequence = len(sequence)
    p_zero = pow(10,expzero/length_sequence)
    p_nan = pow(10, expnan/length_sequence)
    index_subida = buscar_locacion(mls,sequence[0])
    for travel in sequence[1:]:
        horario = get_horario(timestamps[travel_counter].time())
        # buscar pik en tpm
        index_bajada = buscar_locacion(mls,travel)
        if(index_bajada < 0 or index_subida < 0):
            pik = p_nan
        else:
            pik_base = get_pik_base(tpm,index_subida,index_bajada)
            pik_bonus = get_pik_bonus_2(tpm,index_subida,index_bajada,horario)
            pik = pik_base + pik_bonus
        if(pik != pik):
            pik = p_nan
        elif(pik == 0):
            pik = p_zero
        # sumar log10
        similarity += np.log10(pik)
        index_subida = index_bajada
        travel_counter += 1
    return similarity

# Funcion que construye la matriz de identificacion en que cada indice corresponde
# a la similitud entre la i-esima tpm y la j-esima secuencia, obtenidas a partir de un
# perfil de usuario y un periodo de identificacion.
# len(users_profiles) == len(users_sequences)
# asume que los usuarios de users_profiles y users_sequences son los mismos
# get_identification_matrix; get_profiles(...) get_sequences(...) -> [[int]]
def get_identification_matrix(users_profiles,users_sequences):
    i = 0
    j = 0
    limit = np.min((len(users_profiles),len(users_sequences)))
    identification_matrix = np.zeros((limit,limit))
    for profile in users_profiles:
        tpm = profile['tpm']
        id_user = profile['user_id']
        mls = profile['mls']
        for data_sequence in users_sequences:
            identification_matrix[i,j] = get_similarity(tpm,mls,data_sequence['sequence'])
            j += 1
            if(j >= limit):
                break
        i += 1
        j = 0
        if(i >= limit):
            break
    return identification_matrix

# Funcion que construye la matriz de identificacion en que cada indice corresponde
# a la similitud entre la i-esima tpm y la j-esima secuencia, obtenidas a partir de un
# perfil de usuario y un periodo de identificacion.
# len(users_profiles) == len(users_sequences)
# asume que los usuarios de users_profiles y users_sequences son los mismos
# get_identification_matrix; get_profiles(...) get_sequences(...) -> [[int]]
def get_spatiotemporal_identification_matrix(users_profiles,users_sequences):
    i = 0
    j = 0
    limit = np.min((len(users_profiles),len(users_sequences)))
    identification_matrix = np.zeros((limit,limit))
    for profile in users_profiles:
        tpm = profile['tpm']
        id_user = profile['user_id']
        mls = profile['mls']
        for data_sequence in users_sequences:
            identification_matrix[i,j] = get_spatiotemporal_similarity(tpm,mls,data_sequence['sequence'],data_sequence['timestamps'])
            j += 1
            if(j >= limit):
                break
        i += 1
        j = 0
        if(i >= limit):
            break
    return identification_matrix


# Funcion que construye la matriz de identificacion en que cada indice corresponde
# a la similitud entre la i-esima tpm y la j-esima secuencia, obtenidas a partir de un
# perfil de usuario y un periodo de identificacion.
# len(users_profiles) == len(users_sequences)
# asume que los usuarios de users_profiles y users_sequences son los mismos
# get_identification_matrix; get_profiles(...) get_sequences(...) -> [[int]]
def get_spatiotemporal_identification_matrix_2(users_profiles,users_sequences):
    i = 0
    j = 0
    limit = np.min((len(users_profiles),len(users_sequences)))
    identification_matrix = np.zeros((limit,limit))
    for profile in users_profiles:
        tpm = profile['tpm']
        id_user = profile['user_id']
        mls = profile['mls']
        for data_sequence in users_sequences:
            identification_matrix[i,j] = get_spatiotemporal_similarity_2(tpm,mls,data_sequence['sequence'],data_sequence['timestamps'])
            j += 1
            if(j >= limit):
                break
        i += 1
        j = 0
        if(i >= limit):
            break
    return identification_matrix

# Funcion que construye la matriz de identificacion en que cada indice corresponde
# a la similitud entre la i-esima tpm y la j-esima secuencia, obtenidas a partir de un
# perfil de usuario y un periodo de identificacion.
# len(users_profiles) == len(users_sequences)
# asume que los usuarios de users_profiles y users_sequences son los mismos
# get_identification_matrix; get_profiles(...) get_sequences(...) -> [[int]]
def get_spatiotemporal_identification_matrix_3(users_profiles,users_sequences):
    i = 0
    j = 0
    limit = np.min((len(users_profiles),len(users_sequences)))
    identification_matrix = np.zeros((limit,limit))
    for profile in users_profiles:
        tpm = profile['tpm']
        id_user = profile['user_id']
        mls = profile['mls']
        for data_sequence in users_sequences:
            identification_matrix[i,j] = get_spatiotemporal_similarity_3(tpm,mls,data_sequence['sequence'],data_sequence['timestamps'])
            j += 1
            if(j >= limit):
                break
        i += 1
        j = 0
        if(i >= limit):
            break
    return identification_matrix

#Funcion que entrega indice de horario de un tiempo
#noche, punta mañana, medio dia, punta tarde
#get_horario: datetime -> int
def get_horario(tiempo):
    noc = datetime.time(21,30)
    pma = datetime.time(6,30)
    md = datetime.time(12,30)
    pta = datetime.time(17,30)

    if tiempo < pma or tiempo > noc:
        return 0
    elif tiempo < md:
        return 1
    elif tiempo < pta:
        return 2
    else:
        return 3
# Funcion que entrega los perfiles de usuario a partir de los registros 
# de transacciones. Utilizar con los registros del periodo de creacion de 
# perfiles.
# get_profiles: [string] [Timestamp] [string] [string] -> [{'user_id': string, 'mls':[int], 
#                                               'tpm':[[int]], 'nvisitas': int}]
def get_spatiotemporal_profiles(ids, timestamps, par_subidas, par_bajadas):
    # se inicializan las variables con los valores de la primera transaccion
    matrix_size = 30
    users_profiles= [] # arreglo de diccionarios
    First = True
    last_id = -1
    mls = []
    tpm = []
    nvisitas = []
    for transaction in zip(ids,timestamps,par_subidas,par_bajadas):
        user_id = transaction[0]
        timestamp = transaction[1]
        horario = get_horario(timestamp.time()) 
        par_subida = transaction[2]
        par_bajada = transaction[3]
        # no se pierde el paradero de bajada, porque cuando no hay subida no se puede estimar la bajada
        if (par_subida!=par_subida):
            continue 
        if First:
            last_id = user_id
            tpm = np.zeros((matrix_size*4,matrix_size))
            mls = [par_subida]
            last_stop = par_subida
            last_stop_index = horario
            nvisitas = [0]
            First = False
        # guardar perfil y construir nueva TPM y mls no vacia para que no se caiga
        if user_id!=last_id:
            users_profiles.append(create_spatiotemporal_profile(last_id,mls,nvisitas,tpm))
            last_id = user_id
            tpm = np.zeros((matrix_size*4,matrix_size))
            mls = [par_subida]
            last_stop = par_subida
            last_stop_index = horario
            nvisitas = [0]

        index_subida = buscar_locacion(mls,par_subida)
        # si la subida no había sido visitada se debe agregar al mls
        if (index_subida < 0):
            if(len(mls)<matrix_size/4-1):
                mls.append(par_subida)
                nvisitas.append(1)
                index_subida = len(mls) - 1
                if(par_subida!=last_stop):
                    tpm[last_stop_index,index_subida] +=1
                # si la bajada no se pudo calcular solo se considera la subida y 
                # se deja para calcular tpm en la proxima ronda 
                if (par_bajada!=par_bajada):
                    last_stop = par_subida
                    last_stop_index = (index_subida*4+horario)
                else:
                    index_bajada = buscar_locacion(mls,par_bajada)
                    # si la bajada no se había visitado antes, agregar bajada y sumar nvisitas 
                    if (index_bajada < 0):
                        mls.append(par_bajada)
                        nvisitas.append(1)
                        index_bajada = len(mls) - 1
                        tpm[(index_subida*4+horario),index_bajada] +=1
                    # sumar nvisita 
                    else:
                        if(index_subida!=index_bajada):
                            nvisitas[index_bajada] = nvisitas[index_bajada]+1
                            tpm[(index_subida*4+horario),index_bajada] +=1
                    last_stop = par_bajada
                    last_stop_index = (index_bajada*4+horario)
        else:
            nvisitas[index_subida] = nvisitas[index_subida]+1
            if(par_subida!=last_stop):
                    tpm[last_stop_index,index_subida] +=1
            # subida estaba de antes y no hay bajada
            # REVISAR SI ESTO NO ES REDUNDANTE!
            if (par_bajada!=par_bajada):
                last_stop = par_subida
                last_stop_index = (index_subida*4+horario)
            # hay subida y bajada
            else:
                index_bajada = buscar_locacion(mls,par_bajada)
                # hay bajada pero no estaba antes
                if (index_bajada<0):
                    if(len(mls)<matrix_size/4-1):
                        mls.append(par_bajada)
                        last_stop = par_bajada
                        nvisitas.append(1)
                        index_bajada = len(mls) - 1
                        last_stop_index = (index_bajada*4+horario)
                        tpm[(index_subida*4+horario),index_bajada] +=1
                    else:
                        last_stop = par_subida
                        last_stop_index = (index_subida*4+horario)
                # subida y bajada estaban de antes
                else:
                    if(index_bajada!=index_subida):
                        nvisitas[index_bajada] = nvisitas[index_bajada]+1
                        tpm[(index_subida*4+horario),index_bajada] +=1
                        last_stop = par_bajada
                        last_stop_index = (index_bajada*4+horario)
    #agrego el ultimo perfil
    users_profiles.append(create_spatiotemporal_profile(last_id,mls,nvisitas,tpm))

    return users_profiles


# Funcion que entrega las secuencias de usuario a partir de los registros de 
# transacciones. Utilizar con los registros del periodo de identificacion.
# get_sequences: [string] [string] [string] -> [{'user_id': string, 'mls':[int], 
#                                               'sequence':[string], 'nvisitas': int}]
def get_spatiotemporal_sequences(ids, timestamps, par_subidas, par_bajadas):
    # se inicializan las variables con los valores de la primera transaccion
    profiles= [] # arreglo de diccionarios
    First = True
    # inicializo para despues usarlas
    last_id = -22
    mls = []
    nvisitas = []
    sequence = []
    timestamp_sequence = []
    for transaction in zip(ids,timestamps,par_subidas,par_bajadas):
        id_user = transaction[0]
        timestamp = transaction[1]
        par_subida = transaction[2]
        par_bajada = transaction[3]
        if (par_subida!=par_subida):
            continue 
        if First:
            last_id = id_user
            mls = [par_subida]
            sequence = [par_subida]
            timestamp_sequence = [timestamp]
            last_stop = par_subida
            nvisitas = [0]
            counter = 1
            First = False
        if id_user!=last_id:       
            profiles.append(create_sequence(last_id,mls,nvisitas,sequence,timestamp_sequence))
            last_id = id_user
            mls = [par_subida]
            sequence = [par_subida]
            timestamp_sequence = [timestamp]
            last_stop = par_subida
            nvisitas = [0]
            counter = 1
            
        index_subida = buscar_locacion(mls,par_subida)
        # si la subida no había sido visitada se debe agregar al mls
        if (index_subida < 0):
            mls.append(par_subida)
            nvisitas.append(1)
            index_subida = len(mls) - 1
            sequence.append(par_subida)
            timestamp_sequence.append(timestamp)
            # si la bajada no se pudo calcular solo se considera la subida y se deja para calcular tpm en la proxima ronda 
            if (par_bajada!=par_bajada):
                last_stop = par_subida
                #print "Iteración n°: " + str(counter) + " , no se pudo estimar la bajada"
            else:
                last_stop = par_bajada
                sequence.append(par_bajada)
                timestamp_sequence.append(timestamp)
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
                sequence.append(par_subida)
                timestamp_sequence.append(timestamp)
            # subida estaba de antes y no hay bajada
            # REVISAR SI ESTO NO ES REDUNDANTE!
            if (par_bajada!=par_bajada):
                last_stop = par_subida
            # hay subida y bajada
            else:
                sequence.append(par_bajada)
                timestamp_sequence.append(timestamp)
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
    profiles.append(create_sequence(last_id,mls,nvisitas,sequence,timestamp_sequence))

    return profiles



# Funcion que entrega los perfiles de usuario a partir de los registros 
# de transacciones. Utilizar con los registros del periodo de creacion de 
# perfiles.
# get_profiles: [string] [Timestamp] [string] [string] -> [{'user_id': string, 'mls':[int], 
#                                               'tpm':[[int]], 'nvisitas': int}]
def get_spatiotemporal_profiles_2(ids, timestamps, par_subidas, par_bajadas):
    # se inicializan las variables con los valores de la primera transaccion
    matrix_size = 30
    users_profiles= [] # arreglo de diccionarios
    First = True
    last_id = -1
    mls = []
    tpm = []
    nvisitas = []
    for transaction in zip(ids,timestamps,par_subidas,par_bajadas):
        user_id = transaction[0]
        timestamp = transaction[1]
        horario = get_horario(timestamp.time()) 
        par_subida = transaction[2]
        par_bajada = transaction[3]
        # no se pierde el paradero de bajada, porque cuando no hay subida no se puede estimar la bajada
        if (par_subida!=par_subida):
            continue 
        if First:
            last_id = user_id
            tpm = np.zeros((matrix_size*4,matrix_size))
            mls = [par_subida]
            last_stop = par_subida
            last_stop_index = horario
            nvisitas = [0]
            First = False
        # guardar perfil y construir nueva TPM y mls no vacia para que no se caiga
        if user_id!=last_id:
            users_profiles.append(create_spatiotemporal_profile_2(last_id,mls,nvisitas,tpm))
            last_id = user_id
            tpm = np.zeros((matrix_size*4,matrix_size))
            mls = [par_subida]
            last_stop = par_subida
            last_stop_index = horario
            nvisitas = [0]

        index_subida = buscar_locacion(mls,par_subida)
        # si la subida no había sido visitada se debe agregar al mls
        if (index_subida < 0):
            if(len(mls)<matrix_size/4-1):
                mls.append(par_subida)
                nvisitas.append(1)
                index_subida = len(mls) - 1
                if(par_subida!=last_stop):
                    tpm[last_stop_index,index_subida] +=1
                # si la bajada no se pudo calcular solo se considera la subida y 
                # se deja para calcular tpm en la proxima ronda 
                if (par_bajada!=par_bajada):
                    last_stop = par_subida
                    last_stop_index = (index_subida*4+horario)
                else:
                    index_bajada = buscar_locacion(mls,par_bajada)
                    # si la bajada no se había visitado antes, agregar bajada y sumar nvisitas 
                    if (index_bajada < 0):
                        mls.append(par_bajada)
                        nvisitas.append(1)
                        index_bajada = len(mls) - 1
                        tpm[(index_subida*4+horario),index_bajada] +=1
                    # sumar nvisita 
                    else:
                        if(index_subida!=index_bajada):
                            nvisitas[index_bajada] = nvisitas[index_bajada]+1
                            tpm[(index_subida*4+horario),index_bajada] +=1
                    last_stop = par_bajada
                    last_stop_index = (index_bajada*4+horario)
        else:
            nvisitas[index_subida] = nvisitas[index_subida]+1
            if(par_subida!=last_stop):
                    tpm[last_stop_index,index_subida] +=1
            # subida estaba de antes y no hay bajada
            # REVISAR SI ESTO NO ES REDUNDANTE!
            if (par_bajada!=par_bajada):
                last_stop = par_subida
                last_stop_index = (index_subida*4+horario)
            # hay subida y bajada
            else:
                index_bajada = buscar_locacion(mls,par_bajada)
                # hay bajada pero no estaba antes
                if (index_bajada<0):
                    if(len(mls)<matrix_size/4-1):
                        mls.append(par_bajada)
                        last_stop = par_bajada
                        nvisitas.append(1)
                        index_bajada = len(mls) - 1
                        last_stop_index = (index_bajada*4+horario)
                        tpm[(index_subida*4+horario),index_bajada] +=1
                    else:
                        last_stop = par_subida
                        last_stop_index = (index_subida*4+horario)
                # subida y bajada estaban de antes
                else:
                    if(index_bajada!=index_subida):
                        nvisitas[index_bajada] = nvisitas[index_bajada]+1
                        tpm[(index_subida*4+horario),index_bajada] +=1
                        last_stop = par_bajada
                        last_stop_index = (index_bajada*4+horario)
    #agrego el ultimo perfil
    users_profiles.append(create_spatiotemporal_profile_2(last_id,mls,nvisitas,tpm))

    return users_profiles