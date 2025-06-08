import sys
import os
# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer, PageBreak, Frame, PageTemplate
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.platypus import HRFlowable
from reportlab.lib.units import inch

from pathlib import Path
import sys, os
from datetime import datetime
import numpy as np
from PIL import Image as PILImage
from io import BytesIO



# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src import db_utils

# Now you can import settings
import settings

title_style = ParagraphStyle(
	name="CustomStyle",
	fontName="Helvetica-Bold",
	fontSize=24,
	leading=16,
	textColor=settings.swto_blue,
	alignment=TA_CENTER,
	spaceBefore=10,
	spaceAfter=10,
	)

right_aligned_style = ParagraphStyle(
	name="RightAligned",
	alignment=TA_RIGHT
)

CenteredAligned = ParagraphStyle(
	name='CenteredAligned',
	alignment=TA_CENTER
)

def get_percent_change(val1, val2):
	if val2 == 0:
		return ((val1 - val2) / (val2 + 1)) * 100
	else:
		return ((val1 - val2) / (val2)) * 100

def bld_stat_color(value, threshold=None, arrow=False, percentage=True):
	"""
	Format a statistic with color and optional arrows.

	Args:
		value (float): The numeric value to evaluate.
		threshold (float, optional): A static threshold for comparison.
		arrow (bool, optional): Whether to add an up/down arrow for percent change.

	Returns:
		Paragraph: A styled paragraph with the appropriate color and symbol.
		"""
	color = colors.black
	symbol = ""
	styles = getSampleStyleSheet()
	
	if threshold is not None:
		# Static threshold check (green if below, red if above)
		color = colors.green if value < threshold else colors.red
	else:
		# Percent change logic
		color = colors.green if value < 0 else colors.red
		if arrow:
			symbol = "&#x2193;" if value < 0 else "&#x2191;"  # Unicode arrows ↓ (2193) and ↑ (2191)
			if value == 0:
				symbol = '-'
	
	# Format the value with 2 decimal places
	formatted_value = f"{value:.2f}% {symbol}".strip() if percentage is True else f'{value:.2f} {symbol}'.strip()
	
	# Create styled paragraph
	return Paragraph(f'<font color="{color}"><strong>{formatted_value}</strong></font>', styles['BodyText'])

def add_logo(canvas, doc):
	logo_path = Path(settings.IMG_ASSETS_PATH) / 'swto_img.png'
	
	x = doc.pagesize[0] - 1.5 * inch
	y = 0.5 * inch
	canvas.drawImage(logo_path, x, y, width=1 * inch, height=1 * inch, preserveAspectRatio=True, mask='auto')

def build_output_path(date, driver_id):
	conn = settings.db_connection()
	c = conn.cursor()
	
	sql = f'SELECT formated_start_date FROM {settings.speedGaugeData} WHERE start_date = ?'
	value = (date,)
	c.execute(sql, value)
	formatted_date = c.fetchone()[0]
	
	sql = f'SELECT driver_name FROM {settings.driverInfo} WHERE driver_id = ?'
	value = (driver_id,)
	c.execute(sql, value)
	result = c.fetchone()[0]
	last_name = result.strip().split()[-1]

	conn.close()
	
	report_dir = settings.IDR_REPORTS_PATH / formatted_date
	report_dir.mkdir(parents=True, exist_ok=True)
	
	file_name = f'{last_name}_{driver_id}_{formatted_date}.pdf'
	
	file_path = report_dir / file_name
	
	return file_path

def build_data_subtable(result):
	img = PILImage.open(BytesIO(result[0]))
	date = Paragraph(f'<strong> {str(result[2])} </strong>')
	location = Paragraph(f'<strong> {str(result[1])} </strong>')
	speed_limit = Paragraph(f'<strong> {str(result[3])} </strong>')
	speed = Paragraph(f'<strong> {str(result[4])} </strong>')
	
	date_lable = Paragraph('<strong>Date</strong>')
	location_lable = Paragraph('<strong>Location</strong>')
	speed_limit_lable = Paragraph('<strong>Speed Limit</strong>')
	speed_lable = Paragraph('<strong>Driver Speed</strong>')
	
	img_buffer = BytesIO()
	img.save(img_buffer, format="PNG")
	img_buffer.seek(0)
	
	rLab_image = Image(img_buffer)
	
	tbl_header = Paragraph(f'<font color={colors.white}><strong>Incident Data</strong></font>', CenteredAligned)
	
	tbl_data = [
		[tbl_header, ''],
		[date_lable, date],
		[location_lable, location],
		[speed_limit_lable, speed_limit],
		[speed_lable, speed]
		]
	
	tbl = Table(tbl_data)
	tbl.setStyle([
		('ALIGN', (0,0), (-1,-1), 'CENTER'),
		('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
		('BACKGROUND', (0,0), (-1,0), settings.swto_blue),
		('SPAN', (0,0), (-1, 0)),
		('ROWBACKGROUNDS', (0,1), (1,-1), ['#ffffff', '#d3d3d3'])
		])
	return tbl

def build_url(url):
	url_link = Paragraph(f'<font color=#0000FF><a href="{url}"><u>Link to Map</u></a></font>')
	return url_link

def build_driver_stats_table(data_packet,  lname, fname):
	'''' sort necessary dictd '''
	page_width = letter[0]
	stats = data_packet['stats']
	plt_paths = data_packet['plt_paths']
	styles = data_packet['styles']
	doc = data_packet['doc']
	
	# rtm data
	rtm_stats = stats['rtm']
	cur_rtm_data = rtm_stats[-1]
	prev_rtm_data = rtm_stats[-2]
	
	# company data
	company_stats = stats['company']
	cur_company_data = company_stats[-1]
	prev_company_data = company_stats[-2]

	
	# driver data
	driver_stats = stats['driver']
	driver_id = driver_stats['driver_id']
	
	cur_driver_data = driver_stats['driver_dicts'][-1]
	prev_driver_data = driver_stats['driver_dicts'][-2]
	
	''' build sub_table data '''
	slope = driver_stats['slope']
	
	percent_change_in_speed = get_percent_change(cur_driver_data['percent_speeding'], prev_driver_data['percent_speeding'])
	
	abs_change_in_speed = cur_driver_data['percent_speeding'] - prev_driver_data['percent_speeding']
	
	percent_from_company_avg = get_percent_change(cur_driver_data['percent_speeding'] ,cur_company_data['average'])
	
	l_sub_table_title = Paragraph(f'<font color=white>Driver Statistics: {lname}</font>', CenteredAligned)
	
	percent_from_rtm_avg = get_percent_change(cur_driver_data['percent_speeding'] ,cur_rtm_data['average'])
	
	''' build sub_table '''
	l_sub_table_data = [
		[
			l_sub_table_title,
			''
			],
		[
			Paragraph('Last Week Percent Speeding'),
			bld_stat_color(prev_driver_data['percent_speeding'], threshold=0.4)
			],
		[
			Paragraph('Percent Change In Speed'),
			bld_stat_color(percent_change_in_speed, arrow=True, percentage=True)
			],
		[
			Paragraph('Absolute Value Of Change In Speed'),
			bld_stat_color(abs_change_in_speed, percentage=False, arrow=True)
			],
		[
			Paragraph(f'Driver Average Percent Speeding'),
			bld_stat_color(driver_stats['avg'], percentage=True, threshold=0.4, arrow=False)
			],
		[
			Paragraph('Current Slope Trajectory of Percent Speeding Data Points'),
			bld_stat_color(driver_stats['slope'], percentage=False, arrow=True)
			]
		]
		
	l_sub_table = Table(
		l_sub_table_data
		)
	
	l_sub_table.setStyle([
		('ALIGN', (0,0), (-1,-1), 'CENTER'),
		('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
		('SPAN', (0,0), (-1,0)),
		('BACKGROUND', (0,0), (-1,0), settings.swto_blue),
		('ROWBACKGROUNDS', (0,1), (1,-1), ['#ffffff', '#d3d3d3'])
		])
	
	''' build main table '''
	img_path = settings.IMG_ASSETS_PATH / 'spear.jpg'
	img = Image(img_path)
	
	w, h = img.drawWidth, img.drawHeight
	aspect_ratio = w / h
	
	adjusted_h = 100
	adjusted_w = adjusted_h * aspect_ratio
	
	adjusted_img = Image(
		img_path,
		width=adjusted_w, height=adjusted_h
		)
	
	# build main table
	main_table_data = [
		[
			'',
			adjusted_img,
			l_sub_table,
			adjusted_img,
			''
			]
		]
	
	main_table = Table(
		main_table_data,
		colWidths = [
			page_width * 0.10,
			page_width * 0.20,
			page_width * 0.40,
			page_width * 0.20,
			page_width * 0.10
			]
		)
	
	main_table.setStyle([
		('ALIGN', (0,0), (-1,-1), 'CENTER'),
		('VALIGN', (0,0), (-1,-1), 'MIDDLE')
		])
	
	
	return main_table

def create_overview_frame(data_packet):
	page_width = letter[0]
	
	stats = data_packet['stats']
	plt_paths = data_packet['plt_paths']
	styles = data_packet['styles']
	doc = data_packet['doc']
	
	# rtm data
	rtm_stats = stats['rtm']
	cur_rtm_data = rtm_stats[-1]
	prev_rtm_data = rtm_stats[-2]
	
	# company data
	company_stats = stats['company']
	cur_company_data = company_stats[-1]
	prev_company_data = company_stats[-2]

	
	# driver data
	driver_stats = stats['driver']
	driver_id = driver_stats['driver_id']
	
	cur_driver_data = driver_stats['driver_dicts'][-1]
	prev_driver_data = driver_stats['driver_dicts'][-2]
	
	driver_graph_path = plt_paths['driver_graph']
	cell_width = page_width * 0.4
	
	percent_change_in_speed = get_percent_change(cur_driver_data['percent_speeding'], prev_driver_data['percent_speeding'])
	
	abs_change_in_speed = cur_driver_data['percent_speeding'] - prev_driver_data['percent_speeding']
	
	percent_from_company_avg = get_percent_change(cur_driver_data['percent_speeding'] ,cur_company_data['average'])
	
	percent_from_rtm_avg = get_percent_change(cur_driver_data['percent_speeding'] ,cur_rtm_data['average'])
	
	driver_graph_img = Image(driver_graph_path)
	
	w, h = driver_graph_img.drawWidth, driver_graph_img.drawHeight
	
	driver_graph_img.drawWidth = cell_width
	
	driver_graph_img.drawHeight = h * (cell_width / w)
	
	driver_name = cur_driver_data['driver_name']
	fname = driver_name.strip().split()[0]
	lname = driver_name.strip().split()[-1]
	
	content = []
	
	'''**** title section ****'''
	title = Paragraph(
		f'Overview for {fname} {lname}',
		title_style
		)
	sub_title1 = Paragraph(
		f'{driver_id}',
		title_style
		)
	
	sub_title2 = Paragraph(
		f'Date Of Report: {cur_driver_data["human_readable_start_date"]}',
		title_style
		)
	content.append(title)
	content.append(sub_title1)
	content.append(sub_title2)
	
	'''**** main stat table ****'''
	tbl1_row1_col2 = Paragraph(f'<font size=14><strong>Percent Speeding</strong></font>', style=CenteredAligned)
	tbl1_row1_col3 = Paragraph(f'<font size=14 color={colors.white}><strong>{cur_driver_data["percent_speeding" ]}</strong></font>', style=CenteredAligned)
	
	tbl1_data = [
		['',
		tbl1_row1_col2,
		tbl1_row1_col3,
		'']
		]
	tbl1 = Table(
		tbl1_data,
		colWidths = [
			page_width * 0.30,
			page_width * 0.20,
			page_width * 0.20,
			page_width * 0.30
			]
		)
	
	tbl1.setStyle([
		('ALIGN', (0,0), (-1,-1), 'CENTER'),
		('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
		('BACKGROUND', (2,0), (2,0), colors.green if cur_driver_data['percent_speeding'] <= 0.4 else colors.red),
		])
	
	
	content.append(Spacer(1,0.5*inch))
	content.append(tbl1)
	content.append(Spacer(1,0.5*inch))
	
	'''**** driver stats table ****'''
	driver_stats_table = build_driver_stats_table(data_packet, lname, fname)
	
	content.append(driver_stats_table)
	content.append(Spacer(1,0.5*inch))
	
	'''**** Comparaative Stats Table ****'''
	l_sub_tbl_data = [
		[
			Paragraph('<font color=white><strong>Company Statistics</strong></font>', style=CenteredAligned),
			'',
			],
		[
			Paragraph('Company Average'),
			bld_stat_color(cur_company_data['average'], threshold=0.4, percentage=True, arrow=False)
			],
		[
			Paragraph('Driver Percent From Company Average'),
			bld_stat_color(percent_from_company_avg, arrow=True, percentage=True)
			],
		[
			Paragraph('Rtm Market Average'),
			bld_stat_color(cur_rtm_data['average'], threshold=0.4, percentage=True, arrow=False)
			],
		[
			Paragraph('Driver Percent From Rtm Market Average'),
			bld_stat_color(percent_from_rtm_avg, arrow=True, percentage=True)
			]
		]
	
	l_sub_tbl = Table(
		l_sub_tbl_data
		)

	l_sub_tbl.setStyle([
		('ALIGN', (0,0), (-1,-1), 'CENTER'),
		('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
		('SPAN', (0,0), (1,0)),
		('BACKGROUND', (0,0), (1,0), settings.swto_blue),
		('ROWBACKGROUNDS', (0,1), (-1,-1), ['#ffffff', '#d3d3d3'])
		])
	
	r_sub_tbl_data = [
		[
			driver_graph_img
			]
		]
	
	r_sub_tbl = Table(
		r_sub_tbl_data
		)
	
	r_sub_tbl.setStyle([
		('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
		('ALIGN', (0,0), (-1,-1), 'CENTER')
		])
	
	c_stats_main_tbl_data = [
		[
			'',
			l_sub_tbl,
			r_sub_tbl,
			'',
			]
		]
	
	c_stats_main_tbl = Table(
		c_stats_main_tbl_data,
		colWidths = [
			page_width * 0.10,
			page_width * 0.30,
			page_width * 0.50,
			page_width * 0.10
			]
		)
	
	content.append(c_stats_main_tbl)
	content.append(PageBreak())
	
	pg2_title = Paragraph(f'Spreadsheet Data For', style=title_style)
	pg2_subtitle = Paragraph(f'{fname} {lname}', style=title_style)
	content.append(pg2_title)
	content.append(pg2_subtitle)
	content.append(Spacer(1,0.5*inch))
	
	driver_data_points = [
		'driver_name',
		'driver_id',
		'percent_speeding',
		'max_speed_non_interstate_freeway',
		'percent_speeding_non_interstate_freeway',
		'max_speed_interstate_freeway',
		'percent_speeding_interstate_freeway',
		'worst_incident_date',
		'incident_location',
		'speed_limit',
		'speed',
		'speed_cap',
		'custom_speed_restriction',
		'distance_driven',
		'url',
		'location',
		'percent_speeding_numerator',
		'percent_speeding_denominator',
		'incidents_interstate_freeway',
		'observations_interstate_freeway',
		'incidents_non_interstate_freeway',
		'observations_non_interstate_freeway',
		'difference',
		'start_date',
		'end_date'
		]
		
	stat_tbl_data = []
	
	for i in driver_data_points:
		if not cur_driver_data[i]:
			insertion = Paragraph('-')
		else:
			info = str(cur_driver_data[i])
			insertion = Paragraph(info)
		
		if i == 'url' and cur_driver_data[i] != None:
			if len(cur_driver_data[i]) > 2:
				insertion = build_url(cur_driver_data[i])
						
		stat_tbl_data.append(
			[
				'',
				Paragraph(i),
				insertion,
				''
				])

	
	stat_tbl = Table(
		stat_tbl_data,
		colWidths = [
			page_width * 0.10,
			page_width * 0.30,
			page_width * 0.30,
			page_width * 0.30
			]
		)
	
	stat_tbl.setStyle([
		('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
		('ROWBACKGROUNDS', (1,0), (2,-1), ['#d3d3d3', '#ffffff'])
		])
	
	content.append(stat_tbl)
	
	conn = settings.db_connection()
	c = conn.cursor()
	
	driver_id = cur_driver_data['driver_id']
	
	sql = f'SELECT speed_map, location, human_readable_start_date, speed_limit, speed, full_speed_map FROM {settings.speedGaugeData} WHERE driver_id = ? AND speed_map NOT NULL ORDER BY start_date ASC'
	value = (driver_id,)
	c.execute(sql, value)
	results = c.fetchall()
	results.reverse()
	conn.close()
	
	''' build speed map table '''
	''' ********************* '''
	
	content.append(PageBreak())
	
	pg3_title = Paragraph(f'Record of Overspeed Events', style=title_style)
	content.append(pg3_title)
	content.append(Spacer(1,0.5*inch))
	
	map_tbl_data = []
	
	col2_w = page_width * 0.30
	col3_w = page_width * 0.50
	
	# only put table in if there are entries in it
	if len(results) > 0:
		map_w = col3_w * 0.75
		aspect_ratio = 2/3
		map_h = map_w * aspect_ratio
		
		full_map_bytes = results[-1][5]
		full_map_stream = BytesIO(full_map_bytes)
		
		full_map = Image(full_map_stream, width=map_w, height=map_h)
		
		full_map_text = Paragraph(
			f'<font color={colors.antiquewhite} size=18><strong>General Map of Incident Locations</strong></font>', style=CenteredAligned
			)
		
		map_tbl_data.append([
			'',
			full_map_text,
			full_map,
			''
			])
		
		for result in results:
			data_subtable = build_data_subtable(result)
			
			img_bytes = result[0]
			img_stream = BytesIO(img_bytes)
			
			map = Image(img_stream, width=map_w, height=map_h)
				
			map_tbl_data.append([
				'',
				data_subtable,
				map,
				'' 
				])
		
		
		stat_tbl = Table(
			map_tbl_data,
			colWidths = [
				page_width * 0.10,
				col2_w,
				col3_w,
				page_width * 0.10
				]
			)
		
		stat_tbl.setStyle([
			('ALIGN', (0,0), (-1,-1), 'CENTER'),
			('VALIGN', (0,0), (-1,-1), 'MIDDLE'),	
			('ROWBACKGROUNDS', (1,1), (2,-1), ['#cad7f2']),
			('BACKGROUND', (1,0), (2,0), settings.swto_blue)
			])
		
		content.append(stat_tbl)
		
		
	return content
	

def create_report(stats, plt_paths):
	rtm_stats = stats['rtm']
	company_stats = stats['company']
	driver_stats = stats['driver']
	
	date = db_utils.get_max_date()
	output_path = build_output_path(date, driver_stats['driver_id'])
	
	frame = Frame(0.5 * inch, 0.5 * inch, 7.5 * inch, 10 * inch, id='main_frame')
	
	doc = SimpleDocTemplate(
		str(output_path),
		pagesize=letter,
		)
	styles = getSampleStyleSheet()
	
	# Add the custom PageTemplate with the logo
	doc.addPageTemplates([
		PageTemplate(id='main_frame', frames=[frame], onPage=add_logo),])
	styles.add(ParagraphStyle(name='centeredText', alignment=TA_CENTER))
	
	data_packet = {
		'stats': stats,
		'plt_paths': plt_paths,
		'styles': styles,
		'doc': doc
	}
	
	content = []
	content.extend(create_overview_frame(data_packet))
	content.append(PageBreak())
	

	doc.build(content, onLaterPages=add_logo)
