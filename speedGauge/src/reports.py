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
from io import BytesIO


# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src import db_utils

# Now you can import settings
import settings

'''
plt_paths dict has these keys:
	rtm_histo_path
	company_histo_path
	avg_plt_path
	median_plt_pth
'''
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


def add_logo(canvas, doc):
	logo_path = Path(settings.IMG_ASSETS_PATH) / 'swto_img.png'
	
	x = doc.pagesize[0] - 1.5 * inch
	y = 0.5 * inch
	canvas.drawImage(logo_path, x, y, width=1 * inch, height=1 * inch, preserveAspectRatio=True, mask='auto')

def build_output_path(date, rtm='chris'):
	conn = settings.db_connection()
	c = conn.cursor()
	
	sql = f'SELECT formated_start_date FROM {settings.speedGaugeData} WHERE start_date = ?'
	value = (date,)
	c.execute(sql, value)
	formatted_date = c.fetchone()[0]

	conn.close()
	
	report_dir = settings.REPORTS_PATH / formatted_date
	report_dir.mkdir(parents=True, exist_ok=True)
	
	file_name = f'{formatted_date}_{rtm}.pdf'
	
	file_path = report_dir / file_name
	
	return file_path

def bld_avg_trend(trend):
	if trend < 0:
		return Paragraph(f'<font color="{colors.green}"><strong>{round(trend, 2)} {settings.down_arrow}</strong></font>')
	else:
		return Paragraph(f'<font color="{colors.green}"><strong>{round(trend, 2)} -</strong></font>')

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

def predict_next_week(dict_list):
	'''
	Predicts the average percentage speeding for the next week using linear regression.
	
	This function takes a list of dictionaries, each containing a weekly average,
	and fits a simple linear regression model to estimate the trend. It then 
	predicts the value for the next week.
	
	Parameters:
		dict_list (list of dict): A list of dictionaries, each containing a key 'average' representing the weekly average.
	
	Returns:
		tuple: A tuple containing:
			- predicted_avg (float): The predicted average for the next week, rounded to two decimal places.
			- slope (float): The slope of the fitted regression line, indicating the rate of change.
	'''
	avg_list = [dict['average'] for dict in dict_list]
	
	week_list = [i +1 for i in range(len(avg_list))]
	
	slope, intercept, = np.polyfit(week_list, avg_list, 1)
	
	next_week = week_list[-1] + 1
	predicted_avg = round(slope * next_week + intercept, 2)
	
	return predicted_avg, slope

def create_overview_frame(data_packet):
	stats = data_packet['stats']
	plt_paths = data_packet['plt_paths']
	styles = data_packet['styles']
	date = db_utils.get_max_date()
	doc = data_packet['doc']
	
	page_width = letter[0]

	rtm_stats = stats['rtm']
	cur_week_rtm = rtm_stats[-1]
	rtm = stats['rtm_name']
	prev_week_rtm = rtm_stats[-2]
	company_stats = stats['company']
	cur_week_company = company_stats[-1]
	
	avg_plt_path = str(plt_paths['avg_plt_path'])
	
	content = []
	
	line_chart_img = Image(avg_plt_path)
	
	# scale the image
	img_w = line_chart_img.drawWidth
	img_h = line_chart_img.drawHeight
	ratio = img_w / img_h
	
	new_w = page_width * 0.8
	new_h = new_w / ratio
	
	line_chart_img.drawWidth = new_w
	line_chart_img.drawHeight = new_h
	
	content.append(Paragraph(f'Overview For {rtm.capitalize()} Market', title_style))
	content.append(Paragraph(f'Week begin date: {date}', title_style))
	content.append(Spacer(1, 20))
	
	line_graph_tbl_data = [
		[
			'',
			line_chart_img,
			''
			]
		]
	
	table = Table(
		line_graph_tbl_data,
		colWidths = [
			page_width * 0.1,
			page_width * 0.8,
			page_width * 0.1
			]
		)
	style = TableStyle([
		('VALIGN', (0,0), (-1,-1), 'MIDDLE')
		])
	table.setStyle(style)
	content.append(table)

	content.append(Spacer(1,0.5*inch))

	# build rtm subtable
	prev_prediction_full = predict_next_week(rtm_stats[:-1])
	cur_prediction_full = predict_next_week(rtm_stats)
	
	cur_prediction = bld_stat_color(cur_prediction_full[0], threshold=0.4, arrow=False, percentage=True)

	prev_prediction = bld_stat_color(prev_prediction_full[0], threshold=0.4, arrow=False, percentage=True)
	
	avg_trend = bld_avg_trend(cur_prediction_full[1])
	
	prev_trend = bld_stat_color(prev_prediction_full[1], threshold=0, arrow=True, percentage=False)
	
	cur_wk_avg_rtm = bld_stat_color(cur_week_rtm['average'], threshold=0.4, arrow=False, percentage=True)

	prev_wk_avg_rtm = bld_stat_color(prev_week_rtm['average'], threshold=0.4, arrow=False, percentage=True)
	
	percent_change_avg_rtm = bld_stat_color(cur_week_rtm['avg_percent_change'], threshold=None, arrow=True, percentage=True)
	
	prev_percent_change_avg_rtm = bld_stat_color(prev_week_rtm['avg_percent_change'], threshold=None, arrow=True, percentage=True)
	
	abs_change_rtm = bld_stat_color(cur_week_rtm['avg_abs_change'], threshold=None, arrow=True, percentage=False)
	
	prev_abs_change_rtm = bld_stat_color(prev_week_rtm['avg_abs_change'], threshold=None, arrow=True, percentage=False)
	
	# buld cur week subtable
	cur_sub_tbl_data = [
		[
			'Average percent_speeding', 
			cur_wk_avg_rtm
		],
		[
			'Percent Change In Average',
			percent_change_avg_rtm
			],
		[
			'Absolute Change In Average',
			abs_change_rtm
		],
		[
			'Predicted Average Next Week',
			cur_prediction
		],
		[
			'Average Trend Direction',
			avg_trend
		]
	]
	cur_sub_tbl = Table(
		cur_sub_tbl_data
		)
		
	# build prev week subtable
	prev_sub_tbl_data = [
		[
			'Average percent_speeding', 
			prev_wk_avg_rtm
		],
		[
			'Percent Change In Average',
			prev_percent_change_avg_rtm
			],
		[
			'Absolute Change In Average',
			prev_abs_change_rtm
		],
		[
			'Predicted Average Next Week',
			prev_prediction
		],
		[
			'Trend Value',
			prev_trend
		]
	]
	prev_sub_tbl = Table(
		prev_sub_tbl_data
		)
	
	# build analysis table
	cur_header = Paragraph(f'<font color="white"><strong>Current RTM Market Stats</strong></font>', styles['centeredText'])
	
	prev_header = Paragraph(f'<font color="white"><strong>Last Week Stats</strong></font>', styles['centeredText'])
	analysis_tbl_data = [
		[
			'',
			cur_header,
			'',
			prev_header,
			''
		],
		['',
		cur_sub_tbl,
		'',
		prev_sub_tbl,
		'']
		]
	analysis_tbl = Table(
		analysis_tbl_data,
		colWidths = [
			page_width * 0.1,
			page_width * 0.39,
			page_width * 0.02,
			page_width * 0.39,
			page_width * 0.1
			]
		)
	
	analysis_tbl.setStyle(
		[
			('ALIGN', (0,0), (-1,0), 'CENTER'),
			('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
			('BACKGROUND', (1,0), (1,0), settings.swto_blue),
			('BACKGROUND', (3,0), (3,0), settings.swto_blue)
		]
	)
	
	cur_sub_tbl.setStyle([
		('ROWBACKGROUNDS', (0,0), (-1,-1), ['#ffffff', '#d3d3d3'])
	])

	prev_sub_tbl.setStyle([
		('ROWBACKGROUNDS', (0,0), (-1,-1), ['#ffffff', '#d3d3d3'])
	])
	
	content.append(analysis_tbl)
	
	return content



def create_report(stats, plt_paths):
	rtm_stats = stats['rtm']
	date = db_utils.get_max_date()
	output_path = build_output_path(date)
	
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
	
if __name__ == '__main__':
	import json
	date_list = db_utils.get_all_dates()
	conn = settings.db_connection()
	c = conn.cursor()
	sql = f'SELECT start_date, rtm, stats, plt_paths FROM {settings.analysisStorage} WHERE start_date = ?'
	value = (date_list[-1],)
	c.execute(sql, value)
	result = c.fetchone()

	stats = json.loads(result[2])
	rtm_stats = stats['rtm']
	company_stats = stats['company']
	
	plt_paths = json.loads(result[3])
	conn.close()

	
	create_report(stats, plt_paths)
