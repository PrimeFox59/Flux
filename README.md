# FLUX Project Manager

A comprehensive web-based project management application built with Streamlit, designed specifically for manufacturing and industrial environments to streamline project collaboration, task tracking, and team communication.

## 🎯 Key Features

### Project Management
- **Create & Manage Projects** with detailed information:
  - Project name and description
  - Part name, part number, customer, and model information
  - Team member assignments
  - Project timeline tracking
- **Project Search & Filtering** by creator or project details
- **Member-based Access Control** - Users only see projects they're assigned to
- **Project Chat** - Built-in messaging system for each project

### Task Management
- **Comprehensive Task Tracking:**
  - Task creation with PIC (Person In Charge) assignment
  - Task delegation system with delegator tracking
  - Due date management
  - Task status workflow: To Do → In Progress → Request Approval → Done
  - Actual start time tracking
  - Task completion timestamps
- **Document Management:**
  - Upload documents to tasks
  - Document revision tracking
  - Add notes to uploaded files
  - Secure file storage

### User Management & Security
- **Role-Based Access Control:**
  - **Admin** - Full system access and user management
  - **Manager** - Project oversight and approval authority
  - **Supervisor** - Team coordination and task approval
  - **Staff** - Task execution and project participation
- **User Registration & Approval System**
- **Department and Section Organization**
- **Password Management** with SHA-256 hashing
- **User Status Tracking** (pending/approved)

### Communication Features
- **Project Chat** - Real-time messaging within each project
- **Direct Messaging** - Private conversations between users
- **Unread Message Indicators** - Never miss important updates
- **User Search** - Find and start conversations with any approved user
- **File Sharing** - Attach documents in chat messages

### Analytics & Reporting
- **Dashboard with Statistics:**
  - Total projects count with monthly trends
  - Total tasks count with monthly trends
  - Completed tasks tracking with monthly trends
- **Audit Trail System:**
  - Complete activity logging
  - User action tracking
  - Timestamp records
  - Detailed activity descriptions
- **Recent Activity Feed** on dashboard

### Notification System
- **Real-time Notifications for:**
  - Tasks awaiting approval (for Managers/Supervisors)
  - Unread direct messages
  - Project updates

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- SQLite3 (included with Python)

## 🚀 Installation

1. Clone or download this repository:
```bash
git clone <repository-url>
cd "Flux Project Manager"
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Ensure you have the following files in the same directory:
   - `app.py` (main application file)
   - `gambarlogo.png` (logo image)
   - `icon.png` (page icon)

4. Create the `.streamlit` directory and `config.toml` if needed (optional for custom styling)

## 💻 Usage

1. Run the application:
```bash
streamlit run app.py
```

2. The application will open in your default web browser at `http://localhost:8501`

3. **Default Login Credentials:**
   - **Admin:**
     - Username: `admin123`
     - Password: `zzz`
   - **Manager:**
     - Username: `M123`
     - Password: `zzz`
   - **Supervisor:**
     - Username: `S123`
     - Password: `zzz`

4. **For New Users:**
   - Click "Daftar Akun Baru" (Register New Account)
   - Fill in employee ID, password, full name, department, and section
   - Wait for admin/manager approval
   - Login after approval

## 🏭 Application Workflow

### For Staff Members:
1. **Login** with employee ID and password
2. **View Assigned Projects** in the Projects page
3. **Work on Tasks:**
   - Start tasks assigned to you
   - Upload documents/deliverables
   - Request approval when complete
4. **Communicate:**
   - Chat within project channels
   - Send direct messages to team members
5. **Track Progress** in the Dashboard

### For Supervisors:
- All Staff capabilities, plus:
- **Approve Task Completion** for your team members
- **Create and Delegate Tasks**
- **Monitor Team Progress**

### For Managers:
- All Supervisor capabilities, plus:
- **Create New Projects** and assign team members
- **Edit Project Details**
- **Approve New Users**
- **Change User Roles**
- **Delete Projects** if needed
- **View Complete Audit Trail**

### For Admins:
- Complete system control:
- **Full User Management:**
  - Approve/reject new registrations
  - Change user roles
  - Reset user passwords
- **Database Maintenance:**
  - Clean orphan data
  - View system integrity
- **Complete Audit Trail Access**
- **All Manager Capabilities**

## 🗃️ Database Structure

The application uses SQLite database (`flux.db`) with the following tables:

### Users Table
- `id` (TEXT, PRIMARY KEY) - Employee ID
- `password` (TEXT) - Hashed password (SHA-256)
- `fullname` (TEXT) - Full name
- `departemen` (TEXT) - Department
- `seksi` (TEXT) - Section
- `role` (TEXT) - User role (Admin/Manager/Supervisor/Staff)
- `status` (TEXT) - Account status (pending/approved)

### Projects Table
- `id` (INTEGER, PRIMARY KEY) - Auto-increment ID
- `name` (TEXT) - Project name
- `description` (TEXT) - Project description
- `part_name` (TEXT) - Part name
- `part_number` (TEXT) - Part number
- `customer` (TEXT) - Customer name
- `model` (TEXT) - Model information
- `creator_id` (TEXT) - Foreign key to users
- `created_at` (TEXT) - Timestamp of creation

### Tasks Table
- `id` (INTEGER, PRIMARY KEY) - Auto-increment ID
- `project_id` (INTEGER) - Foreign key to projects
- `title` (TEXT) - Task title
- `pic_id` (TEXT) - Person In Charge (Foreign key to users)
- `delegator_id` (TEXT) - Task delegator (Foreign key to users)
- `due_date` (TEXT) - Task deadline
- `status` (TEXT) - Task status (To Do/In Progress/Request Approval/Done)
- `created_at` (TEXT) - Task creation timestamp
- `completed_at` (TEXT) - Task completion timestamp
- `actual_start` (TEXT) - Actual start time

### Project_Members Table
- `project_id` (INTEGER) - Foreign key to projects
- `user_id` (TEXT) - Foreign key to users
- Composite Primary Key (project_id, user_id)

### Documents Table
- `id` (INTEGER, PRIMARY KEY) - Auto-increment ID
- `task_id` (INTEGER) - Foreign key to tasks
- `filename` (TEXT) - Original filename
- `filepath` (TEXT) - Server filepath
- `revision_of` (INTEGER) - Foreign key to documents (for revisions)
- `notes` (TEXT) - Document notes

### Chats Table (Project Chat)
- `id` (INTEGER, PRIMARY KEY) - Auto-increment ID
- `project_id` (INTEGER) - Foreign key to projects
- `sender_id` (TEXT) - Foreign key to users
- `message` (TEXT) - Chat message
- `timestamp` (TEXT) - Message timestamp
- `is_read` (INTEGER) - Read status

### Direct_Chats Table (Private Messages)
- `id` (INTEGER, PRIMARY KEY) - Auto-increment ID
- `sender_id` (TEXT) - Foreign key to users
- `receiver_id` (TEXT) - Foreign key to users
- `message` (TEXT) - Chat message
- `timestamp` (TEXT) - Message timestamp
- `is_read` (INTEGER) - Read status

### Audit_Trail Table
- `id` (INTEGER, PRIMARY KEY) - Auto-increment ID
- `timestamp` (TEXT) - Action timestamp
- `user_id` (TEXT) - User who performed action
- `action` (TEXT) - Action type
- `details` (TEXT) - Detailed description

## 🔧 Configuration

### Departments (Alphabetically Sorted)
The application includes 24 predefined departments including:
- 5S-Tpm-Rationalization
- Corporate Planning
- Development & Trial
- Finance & Accounting
- Foundry (Ace, Central, CSM)
- HRD
- Information System
- Maintenance
- Production (Equipment Engineering, Machining)
- Quality (Assurance, Control)
- And more...

### Sections (Alphabetically Sorted)
Over 100 predefined sections covering all manufacturing areas including:
- Core Making & Casting
- Finishing & Fettling
- Heat Treatment
- Machining & Inspection
- Melting & Molding
- Painting & Sand Treatment
- And many more specialized sections

### Customization
You can modify the department and section options in the `app.py` file:
```python
DEPARTEMEN_OPTIONS = sorted([...])
SEKSI_OPTIONS = sorted([...])
```

## 🔒 Security Features

- **Password Hashing** using SHA-256
- **Role-Based Access Control** (RBAC)
- **Foreign Key Constraints** for data integrity
- **Orphan Data Cleanup** to maintain database health
- **Audit Trail** for complete activity tracking
- **Session Management** via Streamlit session state

## 📊 Task Status Workflow

```
To Do → In Progress → Request Approval → Done
  ↑          ↓              ↓
  └──────────┴──────────────┘
     (Can be edited/updated)
```

- **To Do** - Initial state when task is created
- **In Progress** - PIC starts working on the task
- **Request Approval** - PIC requests supervisor/manager approval
- **Done** - Approved by authorized person

## 🛠️ Maintenance & Administration

### Database Maintenance
Admins can access database maintenance tools to:
- Clean orphan data from deleted projects
- View database statistics
- Ensure referential integrity

### User Management
- Approve pending registrations
- Change user roles as needed
- Reset forgotten passwords
- View all user details

### Audit Trail
- Complete activity history
- Filter by user or action type
- Export for compliance reporting

## 📱 Features in Detail

### Project Creation
When creating a project, you can:
1. Enter project name and description
2. Add technical details (part name, number, customer, model)
3. Select team members from approved users
4. Automatically tracks creation date and creator

### Task Management
Tasks include:
- Clear ownership (PIC and delegator)
- Due date tracking
- Multiple status stages
- Document attachments
- Revision control
- Notes and comments

### Communication
- **Project Chat**: All project members can see messages
- **Direct Chat**: Private 1-on-1 conversations
- **Unread Indicators**: Clear notification badges
- **User Search**: Find any approved user to chat with
- **Message History**: All conversations preserved

## 🎨 UI/UX Features

- **Responsive Design** - Works on different screen sizes
- **Custom SVG Icons** - Beautiful, lightweight icons
- **Color-Coded Statistics** - Visual trend indicators
- **Intuitive Navigation** - Sidebar menu system
- **Real-time Updates** - Automatic refresh on actions
- **File Download Links** - Easy document access
- **Formatted Timestamps** - Human-readable dates/times

## 📝 Best Practices

1. **Regular Password Changes** - Change default passwords immediately
2. **Role Assignment** - Assign appropriate roles based on responsibility
3. **Project Organization** - Use clear, descriptive project names
4. **Document Naming** - Use meaningful filenames for uploads
5. **Regular Backups** - Backup `flux.db` and `uploads/` folder regularly
6. **Audit Review** - Regularly check audit trail for unusual activity

## 🐛 Troubleshooting

### Database Issues
- If you encounter foreign key errors, use the database cleanup tool in Admin settings
- Ensure SQLite version supports foreign key constraints

### File Upload Issues
- Check that `uploads/` folder has write permissions
- Verify sufficient disk space

### Login Problems
- Verify user status is "approved" not "pending"
- Check if password was recently reset by admin

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Developer

**Galih Primananda**
- Process Engineer | Software Engineer | System Development
- BNSP Certified Data Scientist

### Connect with Developer:
- 📸 [Instagram](https://instagram.com/glh_prima/)
- 💼 [LinkedIn](https://linkedin.com/in/galihprime/)
- 🐙 [GitHub](https://github.com/PrimeFox59)
- 📁 [Portfolio](https://drive.google.com/drive/folders/11ov7TpvOZ3m7k5GLRAbE2WZFbGVK2t7i?usp=sharing)
- 🤝 [Fastwork for Services & Collaboration](https://fastwork.id/user/glh_prima)

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page or contact the developer.

## 🔄 Version History

- **Version 1.0** (December 2025)
  - Initial release
  - Complete project management system
  - User management with role-based access
  - Task tracking with approval workflow
  - Document management
  - Dual chat system (project & direct)
  - Audit trail system
  - Dashboard analytics

## 🙏 Acknowledgments

- Built with Streamlit
- SQLite for database management
- Python-dateutil for date handling
- Designed for manufacturing and industrial project management

---

**Note:** This application is designed for internal organizational use. Ensure proper security measures are in place for production deployment, including HTTPS, secure password policies, and regular backups.
