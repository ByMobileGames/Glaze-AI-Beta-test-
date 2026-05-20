import os
import random
import threading
import requests

os.environ['KIVY_WINDOW'] = 'sdl2'

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.properties import StringProperty, BooleanProperty, ListProperty, NumericProperty
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp

try:
    from plyer import vibrator
except ImportError:
    vibrator = None

# --- GROQ API KONFİQURASİYASI (ÜSTÜÖRTÜLÜ VƏ TƏHLÜKƏSİZ) ---
# 🔥 Kodda açar yoxdur! APK yığılanda və ya sistemdə təyin olunan mühit dəyişənindən oxunur.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

TARGET_DIR = "/storage/emulated/0/AppProjects/"
USER_AVATAR_PATH = os.path.join(TARGET_DIR, "avatar.png")
CAMERA_ICON_PATH = os.path.join(TARGET_DIR, "camera_icon.png")
GALLERY_ICON_PATH = os.path.join(TARGET_DIR, "gallery_icon.png")

Window.clearcolor = (0.02, 0.03, 0.06, 1)

KV_DATA = '''
<MessageBubble>:
    orientation: 'horizontal'
    size_hint_y: None
    height: max(msg_label.texture_size[1] + 30, 65)
    padding: [15, 5, 15, 5]
    spacing: 12

    Widget:
        size_hint_x: 0.2 if root.sender == 'user' else None
        width: 1 if root.sender == 'bot' else 1

    BoxLayout:
        size_hint: (None, None)
        size: (45, 45) if (root.sender == 'bot' and root.has_logo) else (1, 1)
        opacity: 1 if (root.sender == 'bot' and root.has_logo) else 0
        pos_hint: {'top': 0.95}
        Image:
            id: bot_pfp
            source: app.current_logo_path if app.current_logo_path else ''
            size_hint: (1, 1)
            allow_stretch: True

    BoxLayout:
        id: msg_layout
        size_hint_x: 0.8
        padding: [15, 12, 15, 12]
        canvas.before:
            Color:
                rgba: (0.13, 0.17, 0.25, 0.8) if root.sender == 'bot' else app.theme_color
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [18, 18, 18, 2] if root.sender == 'bot' else [18, 18, 2, 18]

        Label:
            id: msg_label
            text: root.text
            font_size: '15sp'
            text_size: self.width, None
            size_hint_y: None
            height: self.texture_size[1]
            valign: 'middle'
            halign: 'left'
            color: (1, 1, 1, 1)

    Widget:
        size_hint_x: 0.2 if root.sender == 'bot' else None
        width: 1 if root.sender == 'user' else 1

<AttachmentMenu>:
    size_hint: (None, None)
    size: ('220dp', '140dp')
    orientation: 'vertical'
    padding: [20, 15, 20, 15]
    spacing: 12
    canvas.before:
        Color:
            rgba: (0.12, 0.14, 0.2, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [16, 16, 16, 16]
    
    BoxLayout:
        orientation: 'horizontal'
        spacing: 15
        Image:
            source: app.camera_icon if app.camera_icon_exists else 'atlas://data/images/defaulttheme/camera_normal'
            size_hint: (None, None)
            size: ('26dp', '26dp')
            pos_hint: {'center_y': 0.5}
            allow_stretch: True
        Label:
            text: "Kamera"
            font_size: '16sp'
            bold: True
            halign: 'left'
            valign: 'middle'
            text_size: self.size
    
    BoxLayout:
        orientation: 'horizontal'
        spacing: 15
        Image:
            source: app.gallery_icon if app.gallery_icon_exists else 'atlas://data/images/defaulttheme/action_view'
            size_hint: (None, None)
            size: ('26dp', '26dp')
            pos_hint: {'center_y': 0.5}
            allow_stretch: True
        Label:
            text: "Galeri"
            font_size: '16sp'
            bold: True
            halign: 'left'
            valign: 'middle'
            text_size: self.size
            
    Label:
        text: "Hələki İşlək deyil"
        font_size: '13sp'
        color: (0.7, 0.3, 0.3, 1)
        bold: True
        size_hint_y: None
        height: '20dp'
        halign: 'center'

<NavDrawer>:
    size_hint: (None, 1)
    width: '280dp'
    orientation: 'vertical'
    padding: [20, 40, 20, 20]
    spacing: 20
    canvas.before:
        Color:
            rgba: (0.1, 0.11, 0.14, 1)
        Rectangle:
            pos: self.pos
            size: self.size

    Button:
        size_hint: (None, None)
        size: ('240dp', '110dp')
        pos_hint: {'center_x': 0.5}
        background_color: (0, 0, 0, 0)
        on_release: root.shake_and_vibrate(self)
        BoxLayout:
            pos: self.parent.pos if self.parent else (0, 0)
            size: self.parent.size if self.parent else (1, 1)
            orientation: 'vertical'
            Image:
                id: drawer_logo
                source: app.current_logo_path if app.current_logo_path else ''
                allow_stretch: True

    Label:
        text: "Glaze AI v0.1"
        font_size: '22sp'
        bold: True
        color: app.theme_color
        size_hint_y: None
        height: '30dp'

    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: '45dp'
        padding: [15, 5, 15, 5]
        canvas.before:
            Color:
                rgba: (0.16, 0.17, 0.2, 1)
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [10, 10, 10, 10]
        Label:
            text: "🔍   Sohbet arayın"
            font_size: '14sp'
            color: (0.5, 0.5, 0.6, 1)
            halign: 'left'
            text_size: self.size

    Button:
        size_hint_y: None
        height: '50dp'
        background_color: (0, 0, 0, 0)
        on_release: app.root.new_chat_session()
        canvas.before:
            Color:
                rgba: app.theme_color
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [12, 12, 12, 12]
        Label:
            text: "📝  New chat"
            font_size: '16sp'
            bold: True
            color: (1, 1, 1, 1)
            pos: self.parent.pos if self.parent else (0, 0)
            size: self.parent.size if self.parent else (1, 1)
            halign: 'center'
            valign: 'middle'

    Widget:
        size_hint_y: 1

    Label:
        text: "Glaze AI hələki Beta testindədir\\nbuna görə hələki keçmiş chatları\\ngöstərə bilmir"
        font_size: '12sp'
        color: (0.7, 0.7, 0.7, 1)
        text_size: self.size

<ProfilePanel>:
    size_hint: (None, None)
    size: ('270dp', '150dp')
    orientation: 'vertical'
    padding: [15, 15, 15, 12]
    spacing: 14
    canvas.before:
        Color:
            rgba: (0.1, 0.12, 0.16, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [16, 16, 16, 16]
    
    BoxLayout:
        orientation: 'horizontal'
        spacing: 15
        size_hint_y: None
        height: '56dp'
        BoxLayout:
            size_hint: (None, None)
            size: (56, 56)
            pos_hint: {'center_y': 0.5}
            canvas.before:
                Color:
                    rgba: (1, 1, 1, 1) if app.user_avatar_exists else (0.2, 0.25, 0.35, 1)
                Ellipse:
                    source: app.user_avatar_path if app.user_avatar_exists else ''
                    pos: self.pos
                    size: self.size
        Label:
            text: "Təzə İstifadəçi"
            font_size: '17sp'
            bold: True
            halign: 'left'
            valign: 'middle'
            text_size: self.size

    BoxLayout:
        orientation: 'horizontal'
        spacing: 15
        height: '45dp'
        size_hint_y: None
        Button:
            text: "Daxil ol"
            font_size: '14sp'
            bold: True
            background_color: (0, 0, 0, 0)
            canvas.before:
                Color:
                    rgba: (0.16, 0.2, 0.28, 1)
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [8, 8, 8, 8]
        Button:
            text: "Qeydiyyat-\\ndan keç"
            font_size: '14sp'
            bold: True
            background_color: (0, 0, 0, 0)
            canvas.before:
                Color:
                    rgba: (0.16, 0.2, 0.28, 1)
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [8, 8, 8, 8]

    Label:
        text: "Glaze hələki dəstəkləmir"
        font_size: '12sp'
        color: (0.8, 0.2, 0.3, 1)
        bold: True
        halign: 'center'
        size_hint_y: None
        height: '20dp'

<ChatInterface>:
    id: main_root
    
    BoxLayout:
        id: content_container
        orientation: 'vertical'
        size_hint: (1, 1)
        pos_hint: {'x': 0, 'y': 0}
        padding: [0, 0, 0, root.keyboard_offset]

        Widget:
            size_hint_y: None
            height: '75dp'

        ScrollView:
            id: scroll_view
            do_scroll_x: False
            BoxLayout:
                id: chat_box
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: '16dp'
                padding: [16, 16, 16, 16]

        BoxLayout:
            id: input_bar_layout
            orientation: 'horizontal'
            size_hint_y: None
            height: '85dp'
            padding: [12, 12, 12, 12]
            canvas.before:
                Color:
                    rgba: (0.04, 0.06, 0.12, 1)
                Rectangle:
                    pos: self.pos
                    size: self.size

            BoxLayout:
                orientation: 'horizontal'
                padding: [15, 0, 10, 0]
                canvas.before:
                    Color:
                        rgba: (0.11, 0.13, 0.18, 1)
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [24, 24, 24, 24]

                Button:
                    text: "+"
                    font_size: '32sp'
                    color: app.theme_color
                    size_hint_x: None
                    width: '45dp'
                    background_color: (0, 0, 0, 0)
                    on_release: root.toggle_attachment_menu()

                TextInput:
                    id: message_input
                    hint_text: "Mesaj yazın..."
                    hint_text_color: (0.4, 0.4, 0.5, 1)
                    background_color: (0, 0, 0, 0)
                    foreground_color: (1, 1, 1, 1)
                    cursor_color: app.theme_color
                    multiline: False
                    font_size: '16sp'
                    padding: [10, 16, 10, 14]
                    on_text_validate: root.send_message()

                Button:
                    text: ">"
                    font_size: '26sp'
                    bold: True
                    color: app.theme_color
                    size_hint_x: None
                    width: '50dp'
                    background_color: (0, 0, 0, 0)
                    on_release: root.send_message()

    BoxLayout:
        id: header
        orientation: 'horizontal'
        size_hint: (1, None)
        height: '75dp'
        pos_hint: {'x': 0, 'top': 1}
        padding: [15, 0, 15, 0]
        canvas.before:
            Color:
                rgba: (0.04, 0.06, 0.12, 1)
            Rectangle:
                pos: self.pos
                size: self.size

        Button:
            size_hint: (None, None)
            size: ('48dp', '48dp')
            pos_hint: {'center_y': 0.5}
            background_color: (0, 0, 0, 0)
            on_release: root.toggle_drawer()
            canvas:
                Color:
                    rgba: (0.6, 0.6, 0.7, 1)
                Line:
                    points: [self.x + 6, self.y + 32, self.x + 42, self.y + 32]
                    width: 2.5
                Line:
                    points: [self.x + 6, self.y + 24, self.x + 42, self.y + 24]
                    width: 2.5
                Line:
                    points: [self.x + 6, self.y + 16, self.x + 42, self.y + 16]
                    width: 2.5

        Label:
            text: "Glaze AI"
            font_size: '24sp'
            bold: True
            color: (1, 1, 1, 1)
            halign: 'center'
            pos_hint: {'center_y': 0.5}

        Button:
            size_hint: (None, None)
            size: ('55dp', '75dp')
            pos_hint: {'center_y': 0.5}
            background_color: (0, 0, 0, 0)
            on_release: root.toggle_profile_panel()
            BoxLayout:
                id: top_avatar_container
                pos: self.parent.pos if self.parent else (0, 0)
                size: self.parent.size if self.parent else (1, 1)
                padding: [0, 0, 5, 0]
                opacity: 1
                Widget:
                    size_hint_x: 1
                BoxLayout:
                    size_hint: (None, None)
                    size: (48, 48)
                    pos_hint: {'center_y': 0.5}
                    canvas.before:
                        Color:
                            rgba: (1, 1, 1, 1) if app.user_avatar_exists else (0.3, 0.35, 0.45, 1)
                        Ellipse:
                            source: app.user_avatar_path if app.user_avatar_exists else ''
                            pos: self.pos
                            size: self.size
'''

class MessageBubble(BoxLayout):
    text = StringProperty('')
    sender = StringProperty('')
    has_logo = BooleanProperty(False)

class AttachmentMenu(BoxLayout):
    pass

class NavDrawer(BoxLayout):
    is_shaking = BooleanProperty(False)

    def shake_and_vibrate(self, widget):
        if self.is_shaking:
            return
        
        self.is_shaking = True
        try:
            if vibrator:
                vibrator.vibrate(0.1)
        except:
            pass

        orig_x = widget.x
        orig_y = widget.y

        anim = Animation(x=orig_x - dp(8), y=orig_y + dp(5), duration=0.04) + \
               Animation(x=orig_x + dp(8), y=orig_y - dp(5), duration=0.04) + \
               Animation(x=orig_x - dp(6), y=orig_y - dp(3), duration=0.04) + \
               Animation(x=orig_x + dp(6), y=orig_y + dp(4), duration=0.04) + \
               Animation(x=orig_x, y=orig_y, duration=0.04)
        
        anim.bind(on_complete=self.reset_shake)
        anim.start(widget)

    def reset_shake(self, anim, widget):
        self.is_shaking = False

class ProfilePanel(BoxLayout):
    pass

class ChatInterface(FloatLayout):
    drawer_open = BooleanProperty(False)
    menu_open = BooleanProperty(False)
    profile_open = BooleanProperty(False)
    keyboard_offset = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loading_bubble = None  
        self.api_history = [
            {"role": "system", "content": "Sən 'Glaze AI' adında köməkçisən. İstifadəçiyə tam Azərbaycan dilində, qısa, maraqlı və dəqiq cavablar ver."}
        ]
        Window.bind(keyboard_height=self.check_keyboard_height)
        Clock.schedule_once(self.init_chat, 0.1)

    def check_keyboard_height(self, window, height):
        anim = Animation(keyboard_offset=height, duration=0.15, t='out_quad')
        anim.start(self)
        
        if self.menu_open:
            target_y = height + self.ids.input_bar_layout.height + dp(5)
            Animation(y=target_y, duration=0.15, t='out_quad').start(self.attach_menu)
            
        Clock.schedule_once(self.scroll_to_bottom, 0.1)

    def scroll_to_bottom(self, dt):
        self.ids.scroll_view.scroll_y = 0

    def init_chat(self, dt):
        self.ids.chat_box.clear_widgets()
        welcome_txt = "Salam əxi! Glaze interfeysi tam yeniləndi və stabil Llama 3.3 serverinə bağlandı! 🚀"
        self.add_message_with_typing(welcome_txt, 'bot')
        
        self.drawer = NavDrawer()
        self.drawer.x = -self.drawer.width
        self.add_widget(self.drawer)

        self.attach_menu = AttachmentMenu()
        self.attach_menu.pos = (dp(15), -dp(200))
        self.attach_menu.opacity = 0
        self.add_widget(self.attach_menu)

        self.profile_panel = ProfilePanel()
        self.profile_panel.pos = (Window.width - dp(285), Window.height + dp(10))
        self.profile_panel.opacity = 0
        self.add_widget(self.profile_panel)

    def toggle_drawer(self):
        if self.profile_open: self.toggle_profile_panel()
        if self.menu_open: self.toggle_attachment_menu()

        if not self.drawer_open:
            Animation(x=0, duration=0.22, t='out_quad').start(self.drawer)
            self.drawer_open = True
        else:
            Animation(x=-self.drawer.width, duration=0.2, t='in_quad').start(self.drawer)
            self.drawer_open = False

    def toggle_attachment_menu(self):
        if self.profile_open: self.toggle_profile_panel()
        if self.drawer_open: self.toggle_drawer()

        if not self.menu_open:
            target_y = self.keyboard_offset + self.ids.input_bar_layout.height + dp(5)
            self.attach_menu.x = dp(15)
            Animation(y=target_y, opacity=1, duration=0.18, t='out_quad').start(self.attach_menu)
            self.menu_open = True
        else:
            Animation(y=-dp(200), opacity=0, duration=0.15).start(self.attach_menu)
            self.menu_open = False

    def toggle_profile_panel(self):
        if self.menu_open: self.toggle_attachment_menu()
        if self.drawer_open: self.toggle_drawer()

        if not self.profile_open:
            p_pos = (Window.width - dp(285), Window.height - dp(230))
            Animation(pos=p_pos, opacity=1, duration=0.22, t='out_quad').start(self.profile_panel)
            Animation(opacity=0, duration=0.15).start(self.ids.top_avatar_container)
            self.profile_open = True
        else:
            p_pos = (Window.width - dp(285), Window.height + dp(10))
            Animation(pos=p_pos, opacity=0, duration=0.2).start(self.profile_panel)
            Animation(opacity=1, duration=0.2).start(self.ids.top_avatar_container)
            self.profile_open = False

    def on_touch_down(self, touch):
        if self.drawer_open and touch.x > self.drawer.width:
            self.toggle_drawer()
            return True
        if self.profile_open and not self.profile_panel.collide_point(*touch.pos):
            if touch.y < Window.height - dp(230):
                self.toggle_profile_panel()
        return super().on_touch_down(touch)

    def new_chat_session(self):
        self.toggle_drawer()
        self.ids.chat_box.clear_widgets()
        self.api_history = [
            {"role": "system", "content": "Sən 'Glaze AI' adında köməkçisən. İstifadəçiyə tam Azərbaycan dilində, qısa, maraqlı və dəqiq cavablar ver."}
        ]
        self.add_message_with_typing("Yeni söhbət başladı.", 'bot')

    def add_message_with_typing(self, full_text, sender):
        app = App.get_running_app()
        show_logo = bool(sender == 'bot' and app and app.logo_exists)
        
        bubble = MessageBubble(text="", sender=sender, has_logo=show_logo)
        self.ids.chat_box.add_widget(bubble)
        
        current_char_index = 0
        
        def type_char(dt):
            nonlocal current_char_index
            if current_char_index < len(full_text):
                bubble.text += full_text[current_char_index]
                current_char_index += 1
                self.ids.scroll_view.scroll_y = 0
                return True
            return False

        Clock.schedule_once(lambda dt: Clock.schedule_interval(type_char, 0.025), 0.01)
        return bubble

    def send_message(self):
        text = self.ids.message_input.text.strip()
        if not text: return
        
        self.ids.chat_box.add_widget(MessageBubble(text=text, sender='user', has_logo=False))
        self.ids.message_input.text = ''
        Clock.schedule_once(self.scroll_to_bottom, 0.05)
        
        lower_text = text.lower()
        bot_prefix = ""
        
        salam_responses = [
            "Salam! mən Glaze, buyur eşidirəm səni. ",
            "Salam! Yeni bir sualın var? ",
            "Salam, buyur nəsə soruşacaqdın? "
        ]
        necesen_responses = [
            "Yaxşıyam 🙂 sən necəsən? ",
            "Əlayam! Sənin günün necə keçir? ",
            "Şükür hər şey qaydasındadır, səndə nə var nə yox? "
        ]
        
        if "salam" in lower_text:
            bot_prefix += random.choice(salam_responses)
        if "necəsən" in lower_text or "necesen" in lower_text:
            bot_prefix += random.choice(necesen_responses)
            
        self.api_history.append({"role": "user", "content": str(text)})
        
        self.loading_bubble = self.add_message_with_typing("Düşünürəm...", 'bot')
        threading.Thread(target=self.fetch_groq_response_thread, args=(bot_prefix,), daemon=True).start()

    def fetch_groq_response_thread(self, prefix):
        final_text = ""
        success = False
        
        # Əgər açar tapılmasa istifadəçiyə xəbərdarlıq verilsin
        if not GROQ_API_KEY:
            final_text = "Xəta: API açarı tapılmadı! Zəhmət olmasa Buildozer konfiqurasiyasını yoxlayın."
            Clock.schedule_once(lambda dt: self.update_ui_with_response(final_text), 0.01)
            return

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        sanitized_history = []
        for msg in self.api_history:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                sanitized_history.append({
                    "role": str(msg["role"]).strip(),
                    "content": str(msg["content"]).strip()
                })

        payload = {
            "model": GROQ_MODEL,
            "messages": sanitized_history,
            "temperature": 0.6
        }
        
        try:
            response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=12)
            if response.status_code == 200:
                res_json = response.json()
                if "choices" in res_json and len(res_json["choices"]) > 0:
                    api_content = res_json["choices"][0]["message"]["content"]
                    self.api_history.append({"role": "assistant", "content": str(api_content)})
                    final_text = prefix + api_content
                    success = True
                else:
                    final_text = "Serverdən cavab oxunarkən struktur xətası baş oldu."
            else:
                try:
                    err_data = response.json()
                    err_msg = err_data.get("error", {}).get("message", "Daxili xəta")
                    final_text = f"Xəta ({response.status_code}): {err_msg}"
                except:
                    final_text = f"Bağlantı rədd edildi. Status: {response.status_code}"
        except Exception as e:
            final_text = "Şəbəkə xətası baş verdi, internet bağlantısını yoxlayın."

        if not success and final_text == "":
            final_text = "Sorğu icra edilə bilmədi."
                
        Clock.schedule_once(lambda dt: self.update_ui_with_response(final_text), 0.01)

    def update_ui_with_response(self, final_text):
        if self.loading_bubble and self.loading_bubble in self.ids.chat_box.children:
            self.ids.chat_box.remove_widget(self.loading_bubble)
            self.loading_bubble = None
        self.add_message_with_typing(final_text, 'bot')

class GlazeApp(App):
    current_logo_path = StringProperty('')
    user_avatar_path = StringProperty(USER_AVATAR_PATH)
    camera_icon = StringProperty(CAMERA_ICON_PATH)
    gallery_icon = StringProperty(GALLERY_ICON_PATH)
    
    user_avatar_exists = BooleanProperty(False)
    camera_icon_exists = BooleanProperty(False)
    gallery_icon_exists = BooleanProperty(False)
    
    theme_color = ListProperty([0.18, 0.26, 0.42, 1])
    logo_exists = BooleanProperty(False)

    def build(self):
        try:
            Window.softinput_mode = 'below_target'
        except Exception as e:
            print(f"Window mode error: {e}")
        
        Builder.load_string(KV_DATA)
        
        self.user_avatar_exists = os.path.exists(USER_AVATAR_PATH)
        self.camera_icon_exists = os.path.exists(CAMERA_ICON_PATH)
        self.gallery_icon_exists = os.path.exists(GALLERY_ICON_PATH)
        self.setup_random_theme()
        return ChatInterface()

    def setup_random_theme(self):
        themes = [
            {'file': 'glaze_blue.png', 'color': [0.18, 0.26, 0.42, 1]},
            {'file': 'glaze_red.png', 'color': [0.85, 0.15, 0.25, 1]},
            {'file': 'glaze_green.png', 'color': [0.12, 0.58, 0.25, 1]},
            {'file': 'glaze_orange.png', 'color': [0.88, 0.45, 0.12, 1]},
            {'file': 'glaze_purple.png', 'color': [0.55, 0.18, 0.72, 1]}
        ]
        
        chosen = random.choice(themes)
        full_path = os.path.join(TARGET_DIR, chosen['file'])
        
        if os.path.exists(full_path):
            self.current_logo_path = full_path
            self.theme_color = chosen['color']
            self.logo_exists = True
        else:
            for t in themes:
                path = os.path.join(TARGET_DIR, t['file'])
                if os.path.exists(path):
                    self.current_logo_path = path
                    self.theme_color = t['color']
                    self.logo_exists = True
                    break

if __name__ == '__main__':
    GlazeApp().run()
