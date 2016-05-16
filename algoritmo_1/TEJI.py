
# coding: utf-8

# # Tratado de exploración Jupyter I

# ## 1. Preparar los motores

# - ¡Importar importar que el mundo se va a acabar!

# In[2]:

import numpy as np
import pandas as pd
get_ipython().magic(u'matplotlib inline')
import matplotlib.pyplot as plt
import time
import pickle
from __future__ import division
import csv


# - Definición de funciones auxiliares

# In[2]:

# Cargar diccionario de estaciones de metro
dict_metro = {}
with open('/home/cata/Documentos/Datois/Diccionario-EstacionesMetro.csv',mode='r') as infile:
    reader = csv.reader(infile,delimiter=';')
    dict_metro = {rows[5]:rows[7] for rows in reader}


# In[3]:

# Función que estandariza los valores de los paraderos de subida y bajada
def update_vals(row, data=dict_metro):    
    if row.par_subida in data:
        row.par_subida = data[row.par_subida]
    if row.par_bajada in data:
        row.par_bajada = data[row.par_bajada]
    return row


# In[4]:

# Función que busca los indices de los valores en la matriz que coinciden con argumento
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
    


# In[5]:

def queryToCSV(matrix, user_id, user_index, str_diff = ''):
    query = 'id ==' + str(user_id)
    df_query = matrix.query(query)
    file_path =  '/home/cata/Documentos/sequences/' + str(user_id) + '_' + str(user_index) + '_' + str_diff + '.csv'
    df_query.to_csv(path_or_buf=file_path)


# - Leer hace bien 

# In[6]:

#frame = pd.read_csv('/home/cata/Documentos/Datois/etapas100000_abril.csv')
frame = pd.read_csv('/home/cata/Documentos/Datois/etapas_2013_abril_allyearsids_10_100000.csv')
frame.head()


# In[7]:

frame.info()


# - Paso los tiempos de string a timestamp para luego calcular la diferencia entre una transacción y otra

# In[8]:

frame['tiempo_subida'] = pd.to_datetime(frame.tiempo_subida)
frame = frame.sort_values(by=['id', 'tiempo_subida'])


# In[9]:

frame['diferencia_tiempo'] = (frame['tiempo_subida']-frame['tiempo_subida'].shift()).fillna(0)


# In[10]:

frame.head()


# - Elimino las columnas que no usaré (cuidado, correr solo una vez :)

# In[11]:

frame.drop(frame.columns[[2,3,4,5,9,10,11,14,15,16]], axis=1, inplace=True)
frame.head()


# - Falta estandarizar estaciones de metro con dos nombres

# In[12]:

frame = frame.apply(update_vals, axis=1)
frame.head()


# In[13]:

frame.query('id ==24547373')


# In[14]:

frame.query('par_subida == "SANTA ANA L2"')


# - Explorar los periodos de tiempo en distintas locaciones

# In[15]:

## TODO


# ## 2. Crear perfiles de usuarios con las locaciones mínimas y la matriz TPM

# In[16]:

tpm = [] # Transition Probability Matrix (TPM)
mls = [] # minimum location set (mlt)
nvisitas = [] # diccionario contador de visitas a cada locación
profile = {} # diccionario con tpm y mls para cada usuario
users_profiles= [] # arreglo de diccionarios
nlocations = [] # arreglo con el numero de locaciones por cada usuario
nsecuencias = []
last_id = 0
last_stop = ""
last_stop_index = 0
counter = 0
matrix_size = 30 # maximo numero de posiciones admitidas por usuario


# In[17]:

for transaction in zip(frame['id'], frame['par_subida'], frame['par_bajada']):
    counter +=1
    user_id = transaction[0]
    par_subida = transaction[1]
    par_bajada = transaction[2]
    # no se pierde el paradero de bajada, porque cuando no hay subida no se puede estimar la bajada
    if (par_subida!=par_subida):
        continue        
    if (user_id!=last_id):
        # si ya paso una vuelta, agregar TPM y minimum location set a users_profiles
        if(counter>1):
            n_locations = len(mls)
            nlocations.append(n_locations)
            nsecuencias.append(sum(nvisitas))
            tpm = tpm[0:n_locations,0:n_locations]
            tpm = tpm/tpm.sum(axis=1)[:,None]
            profile = {'user_id':last_id,'mls':mls,'tpm':tpm,'nvisitas':nvisitas}
            users_profiles.append(profile)
        # construir nueva TPM y mls no vacia para que no se caiga
        last_id = user_id
        tpm = np.zeros((matrix_size,matrix_size))
        mls = [par_subida]
        last_stop = par_subida
        last_stop_index = 0
        nvisitas = [0]
        counter = 1
    # buscar si la locación ya había sido visitada 
    try:
        index_subida = mls.index(par_subida)
    except ValueError:
        index_subida = -1
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
                try:
                    index_bajada = mls.index(par_bajada)
                except ValueError:
                    index_bajada = -1
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
            try:
                index_bajada = mls.index(par_bajada)
            except ValueError:
                index_bajada = -1
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


# In[18]:

800/100


# - Ejemplo de perfil de usuario

# In[19]:

users_profiles[0]


# ## X. Guardar dataframe abril

# In[20]:

with open('df_abril.pickle', 'w') as f:
    pickle.dump(frame, f)


# ## 3. Explorar los perfiles de usuario

# - Cuantos usuarios habrá en esta muestra?

# In[21]:

numero_usuarios = len(users_profiles)
numero_usuarios


# - Cuantas locaciones habrá por usuario?

# In[22]:

plt.hist(nlocations,28)


# ## 4. Preparar el periodo de identificación

# - Leer hace bien 

# In[23]:

df_id_period = pd.read_csv('/home/cata/Documentos/Datois/etapas_2013_septiembre_allyearsids_10_100000.csv')
df_id_period.head()


# In[24]:

df_id_period['tiempo_subida'] = pd.to_datetime(df_id_period.tiempo_subida)
df_id_period = df_id_period.sort_values(by=['id', 'tiempo_subida'])


# In[25]:

frame['diferencia_tiempo'] = (frame['tiempo_subida']-frame['tiempo_subida'].shift()).fillna(0)


# Reflexion: Debiese utilizar por ahora solo las columnas que me sirven, sino el todos contra todos será muy dificil

# - Elimino las columnas que no usaré (cuidado, correr solo una vez :)

# In[26]:

df_id_period.drop(df_id_period.columns[[2,3,4,5,9,10,11,14,15,16]], axis=1, inplace=True)
df_id_period.head()


# - Estandarizo los paraderos de subida y bajada

# In[27]:

df_id_period = df_id_period.apply(update_vals, axis=1)
df_id_period.head()


# ## X. Guardar dataframe septiembre

# In[28]:

with open('df_septiembre.pickle', 'w') as f:
    pickle.dump(df_id_period, f)


# ## 5. Extraer secuencias y locaciones principales del periodo de identificación

# Debo extraer la secuencia de posiciones de las transacciones, y el arreglo de locaciones mas visitadas

# In[29]:

tpm = [] # Transition Probability Matrix (TPM)
mls = [] # minimum location set (mlt)
nvisitas = [] # diccionario contador de visitas a cada locación
profile = {} # diccionario con tpm y mls para cada usuario
profiles = [] # arreglo de diccionarios
last_id = 0
last_stop = ""
last_stop_index = 0
counter = 0
n_locations = []


# In[30]:

for transaction in zip(df_id_period['id'], df_id_period['par_subida'], df_id_period['par_bajada']):
    counter +=1
    id_user = transaction[0]
    par_subida = transaction[1]
    par_bajada = transaction[2]
    if (par_subida!=par_subida):
        continue        
    if (id_user!=last_id):
        # si ya paso una vuelta, agregar TPM y minimum location set a users_profiles
        if(counter>1):
            n_locations.append(len(mls))
            profile = {'user_id':last_id,'sequence':sequence,'mls':mls,'nvisitas':nvisitas}
            profiles.append(profile)
        last_id = id_user
        # construir mls no vacia para que no se caiga 
        mls = [par_subida]
        sequence = [par_subida]
        last_stop = par_subida
        nvisitas = [0]
        counter = 1
    # buscar si la locación ya había sido visitada 
    try:
        index_subida = mls.index(par_subida)
    except ValueError:
        index_subida = -1
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
            try:
                index_bajada = mls.index(par_bajada)
            except ValueError:
                index_bajada = -1
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
            try:
                index_bajada = mls.index(par_bajada)
            except ValueError:
                index_bajada = -1
            # hay bajada pero no estaba antes
            if (index_bajada<0):
                mls.append(par_bajada)
                index_bajada = len(mls) - 1
                nvisitas.append(1)
            # subida y bajada estaban de antes
            else:
                nvisitas[index_bajada] = nvisitas[index_bajada]+1


# - Por ej. la secuencia 2 es un diccionario con las locaciones minimas, las visitas a esas locaciones, la secuencia y el id del usuario

# In[31]:

# Por ej. el perfil 0 es un diccionario con las locaciones minimas, 
# las visitas a esas locaciones, la secuencia y el id del usuario
profiles[0]


# - Se puede observar que el largo de la secuencia es mayor al de las locaciones minimas

# In[32]:

len(profiles[0]['sequence'])


# In[33]:

len(profiles[0]['mls'])


# - El número total de perfiles de secuencia extraidos es:

# In[34]:

n_users = len(profiles)
n_users


# ## X. Guardar perfiles y secuencias

# In[35]:

with open('users_profiles.pickle', 'w') as f:
    pickle.dump(users_profiles, f)


# In[36]:

with open('profiles.pickle', 'w') as f:
    pickle.dump(profiles, f)


# ## 6. Todos contra todos

# - Primero encuentro el minimo entre el numero de tpms y las secuencias, para que la matriz sea cuadrada

# In[37]:

limit = np.min((n_users,numero_usuarios))
limit


# - Luego comparo todas las tpms contra todas las secuencias

# In[38]:

tpm = []
index_correct = []

idenk = 0
iden = np.zeros((limit,limit))
i = 0
j = 0


# In[39]:

# asume que son los mismos ids o que se saben de antemano
start_time = time.time()
for profile in users_profiles:
    tpm = profile['tpm']
    id_user = profile['user_id']
    mls = profile['mls']
    for sequence in profiles:
        travel_counter = 0
        largo_secuencia = len(sequence['sequence'])
        p_zero = pow(10,-800/largo_secuencia)
        p_nan = pow(10,-800/largo_secuencia)
        #calcular idenk
        for travel in sequence['sequence']:
            # buscar pik en tpm
            try:
                index_bajada = mls.index(travel)
            except ValueError:
                index_bajada = -1
            if(travel_counter > 0):
                if(index_bajada < 0 or index_subida < 0):
                    pik = p_nan
                else:
                    pik = tpm[index_subida, index_bajada]
                if(pik != pik):
                    pik = p_nan
                elif(pik == 0):
                    pik = p_zero
                # sumar log10
                idenk += np.log10(pik)
            index_subida = index_bajada
            travel_counter +=1

        iden[i,j] = idenk
        j+=1
        if(id_user == sequence['user_id']):
            index_correct.append(idenk)
        idenk = 0
        if(j >= limit):
            break
    i += 1
    j = 0
    if(i >= limit):
        break
delta_time = time.time() - start_time


# - Guardar resultados

# with open('objs_10.pickle', 'w') as f:
#     pickle.dump([iden, index_correct, delta_time], f)

# In[7]:

with open('/home/cata/Proyectos/Notebooks & beyond/Notebooks/Normalizasound_2/objs_10.pickle') as f:
    iden, index_correct, delta_time = pickle.load(f)


# ## 7. Análisis de resultados

# - Los indices correctos están en la diagonal, y a pesar de que las secuencias son de distinto largo se logra identificar la correcta

# In[8]:

iden_matrix = np.matrix(iden)
df_ident = pd.DataFrame(iden_matrix)
df_ident.head()


# In[9]:

df_ident.info()


# - Porcentaje de identificaciones correctas

# In[10]:

i = 0
identified_indexs = []
wrong_indexs = []
correct_indexs = []
selected_indexs = []
n_identified = 0
limit = 5168
while (i<limit):
    the_index = np.argmax(iden_matrix[:,i])
    selected_indexs.append(np.max(iden_matrix[:,i]))
    identified_indexs.append(the_index)
    if(the_index!=i):
        wrong_indexs.append(the_index)
    else:
        correct_indexs.append(the_index)
        n_identified += 1
    i += 1


# In[11]:

porcentaje_correcto = n_identified*100/limit
print str(round(porcentaje_correcto,2))+ "%"


# In[12]:

len(correct_indexs)


# Histograma de los indices seleccionados como correctos, y los indices de los correctamente seleccionados

# In[13]:

plt.hist(selected_indexs,40)


# In[14]:

fig, axs = plt.subplots(1,2)
plt.subplot(121)
plt.hist(selected_indexs,40)
plt.subplot(122)
plt.hist(index_correct,40)
plt.show()


# - Se observa redundancia en los incorrectamente identificados, probablemente causado por usuarios que viajan mucho

# In[15]:

x = np.array(identified_indexs)
y = np.bincount(x)
ii = np.nonzero(y)[0]


# In[16]:

frequency_correct = zip(ii,y[ii]) 


# In[17]:

counter = 0
ncounter = 0
freq_max_1 = 0
freq_max_2 = 0
freq_max_3 = 0
for element in frequency_correct:
    if(element[1]>1):
        counter +=1
        ncounter += element[1]
    


# - Cuantos ids se asignan a más de un usuario

# In[18]:

counter


# - A cuantos usuarios?

# In[19]:

ncounter


# - Si quito estos ids, cual es el porcentaje de identificación?

# In[20]:

x = limit-1-ncounter


# In[21]:

(n_identified-counter)/x*100


# - Falta analizar los casos en que el indice correcto es muy bajo

# In[22]:

# TODO


# - Falta ver quienes son los que se mal identifican 

# In[23]:

# TODO


# - Falta ver quienes son los que se identifican con muchos y si son las mismas personas (compatibilidad)

# In[24]:

# TODO


# - Debiese alargar la secuencia si es que es menor que las locaciones de la tpm?<br/>
#     pensar en casos de borde

# In[25]:

# TODO


# - Ordenar ids más usados

# In[26]:

frequency_correct.sort(key = lambda t: t[1], reverse=True)
frequency_correct

