from database.utils.metadata import *
from database.utils.metrics import MetricsRepo
from database.utils.network_items import *
from database.utils.roles import RolesRepo
from database.utils.scrape_accounts import *
from database.utils.session import *
from database.utils.users import *
from database.utils.vkontakte import *
from database.utils.telegram import *
from database.utils.telegram_bot import *
from database.utils.proxies import *
from database.utils.instagram import *
from database.utils.youtube import *
from database.utils.social_network import *
from database.utils.settings import *
from database.utils.tiktok import *


class INITDatabase:
    def __init__(self):
        self.settings_repo = SettingsRepo()
        self.users_repo = UsersRepo()
        self.session_repo = SessionRepo()
        self.scrape_accounts_repo = ScrapeAccountsRepo()
        self.telegram_bot_repo = TelegramBotRepo()
        self.social_networks_repo = SocialNetworksRepo()
        self.proxies_repo = ProxiesRepo()
        self.item_metadata_repo = ItemMetadataRepo()
        self.network_item_repo = NetworkItemsRepo()
        self.metrics_repo = MetricsRepo()
        self.tiktok_repo = TikTokRepo()
        self.youtube_repo = YoutubeRepo()
        self.telegram_repo = TelegramRepo()
        self.vkontakte_repo = VkontakteRepo()
        self.instagram_repo = InstagramRepo()
        self.roles_repo = RolesRepo()


init_database = INITDatabase()
