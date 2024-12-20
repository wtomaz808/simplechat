from config import *

from functions_authentication import *
from functions_content import *
from functions_documents import *
from functions_search import *

from route_frontend_authentication import *
from route_frontend_profile import *
from route_frontend_admin_settings import *
from route_frontend_documents import *
from route_frontend_chats import *
from route_frontend_conversations import *

from route_backend_chats import *
from route_backend_conversations import *
from route_backend_documents import *

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(32) 
app.config['SESSION_TYPE'] = 'filesystem'
app.config['VERSION'] = '0.131'
Session(app)

# =================== Helper Functions ===================
@app.context_processor
def inject_settings():
    settings = get_settings()
    return dict(app_settings=settings)

@app.template_filter('to_datetime')
def to_datetime_filter(value):
    return datetime.fromisoformat(value)

@app.template_filter('format_datetime')
def format_datetime_filter(value):
    return value.strftime('%Y-%m-%d %H:%M')

# =================== Default Routes =====================
@app.route('/')
def index():
    return render_template('index.html')

# =================== Front End Routes ===================
# ------------------- User Authentication Routes ---------
register_route_frontend_authentication(app)

# ------------------- User Profile Routes ----------------
register_route_frontend_profile(app)

# ------------------- Admin Settings Routes --------------
register_route_frontend_admin_settings(app)

# ------------------- Chats Routes -----------------------
register_route_frontend_chats(app)

# ------------------- Conversations Routes ---------------
register_route_frontend_conversations(app)

# ------------------- Documents Routes -------------------
register_route_frontend_documents(app)


# =================== Back End Routes ====================
# ------------------- API Chat Routes --------------------
register_route_backend_chats(app)

# ------------------- API Conversation Routes ------------
register_route_backend_conversations(app)

# ------------------- API Documents Routes ---------------
register_route_backend_documents(app)

if __name__ == '__main__':
    app.run(debug=True)