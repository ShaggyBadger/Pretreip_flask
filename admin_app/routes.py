from tankGauge_app.models import TankCharts, TankData, StoreData, StoreTankMap
from admin.models import Users

@admin_bp.route('/')
def home():
    return render_template('admin/home.html')

