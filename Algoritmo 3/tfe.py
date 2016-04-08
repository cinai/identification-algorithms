# -*- coding: utf-8 -*-
# module tfe: Travel Feature Extracture library

# CUIDADO con los nombres de las columnas, deben ser:
import numpy as np
from geopy.distance import vincenty
import auxiliar_functions
# Auxiliar Functions

def split_sequence_by_weekdays(df_sequence):
	weekday = df_sequence.query('weekday != 5 and weekday != 6')
	weekend = df_sequence.query('weekday == 5 or weekday == 6')
	return [weekday.reset_index(drop=True), weekend.reset_index(drop=True)]	

### Activity Features

## Activity length 

# 30
# get_mean_shortests_activity_length: pandas.DataFrame -> Timedelta
# entrega el promedio semanal de la actividad mas corta de cada dia
# el tiempo de una actividad corresponde a la diferencia de tiempo entre dos viajes
def get_mean_shortests_activity_length(df_sequence):
	last_trip = -1
	last_week_day = -1
	shortest_activities = []
	n_days = -1
	for index, stage in df_sequence.iterrows():
		if index == 0 :
			continue
		weekday = stage.tiempo_subida.weekday()
		if  weekday != last_week_day :
			last_week_day = weekday
			last_trip = -1
			n_days += 1
			shortest_activities.append(np.nan)
		if stage.nviaje != last_trip :
			time_diff = stage.diferencia_tiempo
			if shortest_activities[n_days] != shortest_activities[n_days] or shortest_activities[n_days] > time_diff :
				shortest_activities[n_days] = time_diff

	return np.mean(shortest_activities)

# 30
# get_mean_longest_activity_length: pandas.DataFrame -> Timedelta
# entrega el promedio semanal de la actividad mas larga de cada dia
# el tiempo de una actividad corresponde a la diferencia de tiempo entre dos viajes
def get_mean_longest_activity_length(df_sequence):
	last_trip = -1
	last_week_day = -1
	longest_activities = []
	activities_counter = -1
	for index, stage in df_sequence.iterrows():
		if index == 0 :
			continue
		weekday = stage.tiempo_subida.weekday()
		if  weekday != last_week_day :
			last_week_day = weekday
			last_trip = -1
			activities_counter += 1
			longest_activities.append(np.nan)
		if stage.nviaje != last_trip :
			if longest_activities[activities_counter] != longest_activities[activities_counter] or longest_activities[activities_counter] < stage.diferencia_tiempo :
				longest_activities[activities_counter] = stage.diferencia_tiempo

	return np.mean(longest_activities)

## Regularity
# 36
def get_regularity():
	return 0

### Distance Features

## Travel Distance 
# 33
def get_traveled_distance(df_sequence):
	last_stop = ""
	last_lat = ""
	last_long = ""
	distance = 0
	for index, stage in df_sequence.iterrows():
		par_subida = stage.par_subida
		par_bajada = stage.par_bajada
		if par_subida != par_subida:
			continue
		origin_stop = par_subida
		origin_lat = stage.lat_subida
		origin_long = stage.long_subida         
		if last_stop != "":
			distance += vincenty((last_lat,last_long),(origin_lat,origin_long)).meters
		if par_bajada != par_bajada:
			last_stop = origin_stop
			last_lat = origin_lat
			last_long = origin_long
		else :
			destinatination_stop = par_bajada
			destination_lat = stage.lat_bajada
			destination_long = stage.long_bajada
			distance += vincenty((origin_lat,origin_long),(destination_lat,destination_long)).meters
			last_stop = destinatination_stop
			last_lat = destination_lat
			last_long = destination_long

	return distance/1000
# 30
def get_maximum_travel_distance(df_sequence):
	max_distance = 0
	distance = 0
	for index, stage in df_sequence.iterrows():
		if stage.netapa == 1:
			if distance > max_distance:
				max_distance = distance
			distance = 0
			last_stop = ""
			last_lat = ""
			last_long = ""
		par_subida = stage.par_subida
		par_bajada = stage.par_bajada
		if par_subida != par_subida:
			continue
		origin_stop = par_subida
		origin_lat = stage.lat_subida
		origin_long = stage.long_subida         
		if last_stop != "":
			distance += vincenty((last_lat,last_long),(origin_lat,origin_long)).meters
		if par_bajada != par_bajada:
			last_stop = origin_stop
			last_lat = origin_lat
			last_long = origin_long
		else :
			destinatination_stop = par_bajada
			destination_lat = stage.lat_bajada
			destination_long = stage.long_bajada
			distance += vincenty((origin_lat,origin_long),(destination_lat,destination_long)).meters
			last_stop = destinatination_stop
			last_lat = destination_lat
			last_long = destination_long

	if distance > max_distance:
		max_distance = distance
	return max_distance/1000
# 30
# sin contar los dias que no viaja?
def get_minimum_travel_distance(df_sequence):
	min_distance = 10.0**8
	distance = 0
	for index, stage in df_sequence.iterrows():
		if stage.netapa == 1:
			if distance < min_distance and distance != 0:
				min_distance = distance
			distance = 0
			last_stop = ""
			last_lat = ""
			last_long = ""
		par_subida = stage.par_subida
		par_bajada = stage.par_bajada
		if par_subida != par_subida:
			continue
		origin_stop = par_subida
		origin_lat = stage.lat_subida
		origin_long = stage.long_subida         
		if last_stop != "":
			distance += vincenty((last_lat,last_long),(origin_lat,origin_long)).meters
		if par_bajada != par_bajada:
			last_stop = origin_stop
			last_lat = origin_lat
			last_long = origin_long
		else :
			destinatination_stop = par_bajada
			destination_lat = stage.lat_bajada
			destination_long = stage.long_bajada
			distance += vincenty((origin_lat,origin_long),(destination_lat,destination_long)).meters
			last_stop = destinatination_stop
			last_lat = destination_lat
			last_long = destination_long

	if distance < min_distance and distance != 0:
		min_distance = distance
	return min_distance/1000
# 33. 13 17
# solo considera las subidas
def get_radius_of_gyration(df_sequence):
	locations = []
	rm = np.array([0,0])
	for index, stage in df_sequence.iterrows():
		if stage.par_subida == stage.par_subida:
			locations.append(np.array([stage.lat_subida,stage.long_subida]))
			rm= rm + np.array([stage.lat_subida,stage.long_subida])
	rm = rm/len(locations)
	suma = 0.0
	for r in locations:
		distance = vincenty((r[0],r[1]),(rm[0],rm[1])).meters
		suma = suma + distance**2
	return (suma/len(locations))**0.5

## OD Frecuency
# 36 13 TODO: leer paper
def get_entropy():
	return 0
# Funcion que busca una locacion en el arreglo mls y retorna el indice
# buscar_locacion: [string] string -> int
def buscar_locacion(mls,location):
	try:
		index_location = mls.index(location)
	except ValueError:
		index_location = -1
	return index_location
#36
def get_unc_entropy(df_sequence):
	pis = get_pi_locations(df_sequence)
	la_suma = 0.0
	for pi in pis:
		la_suma = la_suma + pi*np.log2(pi)
	return -la_suma

def get_pi_locations(df_sequence):
	locations = []
	n_locations = []
	for index, stage in df_sequence.iterrows():
		if stage.par_subida == stage.par_subida:
			indice = buscar_locacion(locations,stage.par_subida)
			if indice > -1:
				n_locations[indice] += 1
			else:
				locations.append(stage.par_subida)
				n_locations.append(1)
	la_suma = sum(n_locations)
	n_locations[:] = [x*1.0/la_suma for x in n_locations]
	return n_locations
# 36
def get_random_entropy(df_sequence):
	nl = get_n_different_locations(df_sequence)
	return np.log2(nl)
#36
def get_n_unic_locations():
	return 0
#33 13
# obtiene el numero de locaciones diferentes
# solo considera las subidas
def get_n_different_locations(df_sequence):
	locations = []
	for index, stage in df_sequence.iterrows():
		if stage.par_subida == stage.par_subida:
			locations.append(stage.par_subida)
	the_set = set(locations)
	return len(the_set)
# 30 
def get_percentage_different_last_origin(df_sequence):
	last_origins = []
	last_weekday = -1
	last_origin = ""
	for index, stage in df_sequence.iterrows():
		if stage.weekday != last_weekday and last_weekday > -1:
			last_origins.append(stage.par_subida)
		last_weekday = stage.weekday
		last_origin = stage.par_subida
	last_origins.append(last_origin)
	the_set = list(set(last_origins))
	return len(the_set)*1.0/len(last_origins)*100

# 30 
def get_percentage_different_first_origin(df_sequence):
	first_origins = []
	last_weekday = -1
	for index, stage in df_sequence.iterrows():
		if stage.weekday != last_weekday:
			first_origins.append(stage.par_subida)
		last_weekday = stage.weekday
	the_set = list(set(first_origins))
	return len(the_set)*1.0/len(first_origins)*100
# ?
def get_ROIs():
	return 0

## Regularity
# 33 17 .. en 33 hablan de las PRD PRI, no info
def get_return_degree(df_sequence):
	return 0
# 27 no definen la feature
def get_n_similar_sequences(df_sequence):
	return 0
# 36
def get_regularity_dt(df_sequence):
	return 0

### Temporal Features

## Start Time
# 27 no definen la feature
def get_n_similar_start_times():
	return 0
# 30
# funciona muy mal cuando es irregular
def get_mean_start_time_first_trip(df_sequence):
	start_times = []
	last_weekday = -1
	for index, stage in df_sequence.iterrows():
		if stage.weekday != last_weekday:
			start_times.append(int(auxiliar_functions.hour_to_seconds(stage.tiempo_subida)))
		last_weekday = stage.weekday
	return int(np.mean(start_times))
# 30
# funciona muy mal cuando es irregular
def get_mean_start_time_last_trip(df_sequence):
	end_times = []
	last_weekday = -1
	an_end_time = 0
	for index, stage in df_sequence.iterrows():
		if stage.weekday != last_weekday and last_weekday > -1:
			end_times.append(int(auxiliar_functions.hour_to_seconds(an_end_time)))
		if stage.netapa == 1:
			an_end_time = stage.tiempo_subida
		last_weekday = stage.weekday
	end_times.append(int(auxiliar_functions.hour_to_seconds(an_end_time)))
	return int(np.mean(end_times))
 
## Travel Frequency 

# 
def get_n_days_traveled_before_stop(df_sequence):
	return 0
# 30 27
def get_n_days_traveled(df_sequence):
	traveled_days = 0
	last_weekday = -1
	for index, stage in df_sequence.iterrows():
		if stage.weekday != last_weekday:
			traveled_days += 1
			last_weekday = stage.weekday		
	return 	traveled_days

#30
# hay que rellenar con 0's a la derecha si es que no calzan los dias
def get_n_trips_per_day(df_sequence):
	last_weekday = -1
	last_nviaje = -1
	n_trips_per_day = []
	n_trips = 0
	for index, stage in df_sequence.iterrows():
		if stage.weekday != last_weekday and last_weekday > -1:
			days_diff = abs(stage.weekday - last_weekday)%6
			while(days_diff > 1):
				n_trips_per_day.append(0)
				days_diff -= 1
			n_trips_per_day.append(n_trips)
			n_trips = 0
		last_weekday = stage.weekday		
		if stage.nviaje != last_nviaje:
			n_trips += 1
			last_nviaje = stage.nviaje
	n_trips_per_day.append(n_trips)
	
	return n_trips_per_day
# 41
def get_frequence_regularity(df_sequence):
	return 0

### Sociodemographic Features 

## TODO: check card_type code
# get_card_type: pandas.DataFrame -> int
# Returns the card type of a sequence
# -1 - no information
# 0 - adult
# 1 - other 
def get_card_type(df_sequence):
	card_type = -1
	for index, stage in df_sequence.iterrows():
		if stage.par_subida == stage.par_subida:
			card_type = stage.adulto
			break
	return int(card_type)


###  Variability mode of transport 
# 30
# Considera etapas
def get_percentage_bus_exclusive_days(df_sequence):
	traveled_days = -1.0
	exclusive_bus_days = 0.0
	last_weekday = -1
	bus_exclusive = False
	for index, stage in df_sequence.iterrows():
		if stage.weekday != last_weekday:
			traveled_days += 1	
			last_weekday = stage.weekday
			if bus_exclusive:
				exclusive_bus_days += 1
			bus_exclusive = True
		elif bus_exclusive == False:
			continue
		if stage.tipo_transporte == "METRO":
			bus_exclusive = False
	# debo sumar uno por la ultima corrida de viajes
	traveled_days += 1	
	if bus_exclusive:
		exclusive_bus_days += 1
	return 	exclusive_bus_days/traveled_days*100
# 30
# Considera etapas
def get_percentage_rail_exclusive_days(df_sequence):
	traveled_days = -1.0
	exclusive_metro_days = 0.0
	last_weekday = -1
	metro_exclusive = False
	for index, stage in df_sequence.iterrows():
		if stage.weekday != last_weekday:
			traveled_days += 1	
			last_weekday = stage.weekday
			if metro_exclusive:
				exclusive_metro_days += 1
			metro_exclusive = True
		elif metro_exclusive == False:
			continue
		if stage.tipo_transporte != "METRO":
			metro_exclusive = False
	# debo sumar uno por la ultima corrida de viajes
	traveled_days += 1
	if metro_exclusive:
		exclusive_metro_days += 1
	return 	exclusive_metro_days/traveled_days*100

# inventado
# Considera etapas
def get_percentage_bus_trips():
	bus_counter = 0.0
	for index, stage in df_sequence.iterrows():
		if stage.tipo_transporte != "METRO":
			bus_counter += 1
	return bus_counter/len(df_sequence)*100
    
