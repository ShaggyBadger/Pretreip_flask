from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer, PageBreak, Frame, PageTemplate
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import HRFlowable
from pathlib import Path
import sys, os
from datetime import datetime
from reportlab.lib.units import inch
# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Now you can import settings
import settings








def build_output_path(processing_data):
	date_set = processing_data['date_set']
	current_date = date_set[-1]
	fName = processing_data['driver_name'].split()[0]
	driver_id = processing_data['driver_id']
	
	REPORTS_PATH = Path(settings.REPORTS_PATH)
	
	# Parse date into a datetime object
	date_obj = datetime.strptime(current_date, "%Y-%m-%d %H:%M")

	# Format it into "12Dec2024"
	formatted_date = date_obj.strftime("%d%b%Y").upper()
	
	report_dir = REPORTS_PATH / formatted_date / 'IDR'
	report_dir.mkdir(parents=True, exist_ok=True)
	
	file_name = f'idr_{fName}_{formatted_date}_{driver_id}.pdf'
	
	file_path = report_dir / file_name
	
	return file_path
	














def create_stats_frame(stats, styles, doc):
	content = []
	
	if stats['latest_percent_speeding'] <= 0.4:
		latest_speeding_color = 'green'
	else:
		latest_speeding_color = 'red'
	
	if stats['previous_percent_speeding'] >= 0:
		previous_speeding_color = 'green'
	else:
		previous_speeding_color = 'red'
		
	if stats['abs_change_from_last_week'] == 0:
		abs_change_color = 'green'
		abs_change_arrow = ''
	elif stats['abs_change_from_last _week'] < 0:
		abs_change_color = 'green'
		abs_change_arrow = settings.down_arrow
	else:
		abs_change_color = 'red'
		abs_change_arrow = settings.up_arrow
	
	if stats['percent_change_from_last_week'] == 0:
		percent_change_color = 'green'
		percent_change_arrow = ''
	elif stats['percent_change_from_last_week'] < 0:
		percent_change_color = 'green'
		percent_change_arrow = settings.down_arrow
	else:
		percent_change_color = 'red'
		percent_change_arrow = settings.up_arrow
	
	if stats['rtm_current_avg'] <= 0.4:
		rtm_avg_color = 'green'
	else:
		rtm_avg_color = 'red'
	
	if stats['company_current_avg'] <= 0.4:
		company_avg_color = 'green'
	else:
		company_avg_color = 'red'
	
	if stats['percent_driver_to_market'] == 0:
		percent_driver_to_market_color = 'green'
		percent_driver_to_market_arrow = ''
	elif stats['percent_driver_to_market'] < 0:
		percent_driver_to_market_color = 'green'
		percent_driver_to_market_arrow = settings.down_arrow
	else:
		percent_driver_to_market_color = 'red'
		percent_driver_to_market_arrow = settings.up_arrow
	
	if stats['percent_driver_to_company'] == 0:
		percent_driver_to_company_color = 'green'
		percent_driver_to_company_arrow = ''
	elif stats['percent_driver_to_company'] < 0:
		percent_driver_to_company_color = 'green'
		percent_driver_to_company_arrow = settings.down_arrow
	else:
		percent_driver_to_company_color = 'red'
		percent_driver_to_company_arrow = settings.up_arrow
	
	
	latest_speeding = Paragraph(f'<font color={latest_speeding_color}><strong>{round(stats["latest_percent_speeding"], 2)}%</strong></font>', styles['BodyText'])
	
	previous_speeding = f'<font color={previous_speeding_color}><strong>{round(stats["previous_percent_speeding"], 2)}%</strong></font>'
	
	abs_change_from_last_week = f'<font color={abs_change_color}><strong>{round(stats["abs_change_from_last_week"], 2)} {abs_change_arrow}</strong></font>'
	
	percent_change_from_last_week = f'<font color={percent_change_color}><strong>{round(stats["percent_change_from_last_week"], 2)}% {percent_change_arrow}</strong></font>'
	
	rtm_market_avg = f'<font color={rtm_avg_color}><strong>{round(stats["rtm_current_avg"], 2)}%</strong></font>'

	company_avg = f'<font color={company_avg_color}><strong>{round(stats["company_current_avg"], 2)}%</strong></font>'

	driver_to_rtm = f'<font color={percent_driver_to_market_color}><strong>{round(stats["percent_driver_to_market"], 2)}% {percent_driver_to_market_arrow}</strong></font>'

	driver_to_company = f'<font color={percent_change_color}><strong>{round(stats["percent_driver_to_company"], 2)}% {percent_driver_to_company_arrow}</strong></font>'
	
	
	
	styles.add(ParagraphStyle(
		name='BlueHeading1',
		parent=styles['Heading1'],
		textColor=settings.swto_blue,
		alignment=TA_CENTER
		))
	styles.add(ParagraphStyle(
		name='CenterHeading2',
		parent=styles['Heading2'],
		alignment=TA_CENTER
		))
	styles.add(ParagraphStyle(
		name='CenterHeading3',
		parent=styles['Heading3'],
		alignment=TA_CENTER
		))
	styles.add(ParagraphStyle(
		name='tbl_header',
		parent=styles['Heading3'],
		alignment=TA_CENTER
		))
		
	main_tbl_data = [
		[Paragraph('Driver Analytics', styles['tbl_header']), Paragraph('Driver Conparatives', styles['tbl_header'])]
		]
	
	left_tbl_data =[
		[Paragraph('t1:'), latest_speeding]
		]
	
	right_tbl_data =[
		[Paragraph('t1:'), latest_speeding]
		]
	
	left_sub_tbl = Table(left_tbl_data)
	right_sub_tbl = Table(right_tbl_data)
	
	main_tbl_data.append(
		[left_sub_tbl, right_sub_tbl]
		)
	
	page_width, _ = letter
	margin = 72
	col_widths = (page_width - (2 * margin)) / 2
	
	main_tbl = Table(
		main_tbl_data,
		colWidths = [col_widths, col_widths]
		)
		
	main_tbl.setStyle(TableStyle([
		('VALIGN', (0, 0), (-1, -1), 'TOP'),         # Align content to the top
		('ALIGN', (0, 0), (-1, -1), 'CENTER'),       # Center align content
		('BOX', (0, 0), (-1, -1), 1, 'black'),      # Add borders for clarity
		('GRID', (0, 0), (-1, -1), 0.5, 'gray')     # Add grid lines for table cells
		]))


	content.append(Paragraph(f'Individual Driver Report', styles['BlueHeading1']))
	content.append(Paragraph(f'Driver: {stats["driver_name"]}', styles['CenterHeading2']))

	
	content.append(main_tbl)

	
	
	return content


def create_visualizations_frame(data_packet, styles, doc):
	pass
	
def create_suppliment_frame(data_packet, styles, doc):
	pass


def generate_report(data_packet):
	output_path = build_output_path(data_packet)
	
	doc = SimpleDocTemplate(
		str(output_path),
		pagesize=letter,
		)
	
	styles = getSampleStyleSheet()
	styles.add(ParagraphStyle(name='centeredText', alignment=TA_CENTER))
	
	content = []
	
	stats_frame = create_stats_frame(data_packet, styles, doc)

	content.extend(stats_frame)
	
	doc.build(content)
	
	
	



'''
data_packet['stats'] keys
****************

date_set
driver_name
driver_id
latest_percent_speeding
previous_percent_speeding
abs_change_from_last_week
percent_change_from_last_week
company_current_avg
company_previous_avg
rtm_current_avg
rtm_previous_avg
avg
abs_driver_to_market
percent_driver_to_market
abs_driver_to_company
percent_driver_to_company
median
stdev
stdev_from_mean
abs_avg_change
percent_change_from_avg
abs_median_change
percent_change_from_median



data_packet['graph_paths'] keys:
********************************

lineChart
rtmHistogram
companyHistogram
'''
