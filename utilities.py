def process_settings_update(utils_obj, data_packet):
	for i in data_packet:
		print(f'{i}: {data_packet[i]}')
	return True
