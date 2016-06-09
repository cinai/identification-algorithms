
# coding: utf-8

# # Tratado de exploración Jupyter I

# ## 1. Preparar los motores

# - ¡Importar importar que el mundo se va a acabar!

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import pickle
from __future__ import division
import csv
import tpm_identification
from auxiliar_functions import *


# Cargar diccionario de estaciones de metro
dict_metro = load_metro_dictionary()

# - Leer hace bien 

# In[6]:

#frame = pd.read_csv('/home/cata/Documentos/Datois/etapas100000_abril.csv')
frame = pd.read_csv('/home/cata/Documentos/Datois/etapas_2013_abril_allyearsids_10_100000.csv')


# - Paso los tiempos de string a timestamp para luego calcular la diferencia entre una transacción y otra

# In[8]:

frame['tiempo_subida'] = pd.to_datetime(frame.tiempo_subida)
frame = frame.sort_values(by=['id', 'tiempo_subida'])


# In[9]:

frame['diferencia_tiempo'] = (frame['tiempo_subida']-frame['tiempo_subida'].shift()).fillna(0)


# - Elimino las columnas que no usaré (cuidado, correr solo una vez :)

# In[11]:

frame.drop(frame.columns[[2,3,4,5,9,10,11,14,15,16]], axis=1, inplace=True)

# - Falta estandarizar estaciones de metro con dos nombres

# In[12]:

frame = frame.apply(update_vals, axis=1)

# - Explorar los periodos de tiempo en distintas locaciones

# In[15]:

## TODO


# ## 2. Crear perfiles de usuarios con las locaciones mínimas y la matriz TPM

users_profiles = tpm_identification.get_profiles(frame['id'],frame['par_subida'],frame['par_bajada'])


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

df_id_period['diferencia_tiempo'] = (df_id_period['tiempo_subida']-df_id_period['tiempo_subida'].shift()).fillna(0)


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

profiles = tpm_identification.get_sequences(df_id_period['id'],df_id_period['par_subida'],df_id_period['par_bajada'])
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

# - Luego comparo todas las tpms contra todas las secuencias

start_time = time.time()
iden = tpm_identification.get_identification_matrix(users_profiles,profiles)
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

