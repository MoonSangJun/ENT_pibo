from utils.app_flow import main_menu
from utils.firebase_utils import admin_update_all_users_and_groups

if __name__ == "__main__":
    admin_update_all_users_and_groups()
    main_menu()
