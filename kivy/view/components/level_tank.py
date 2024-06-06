from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import ObjectProperty, NumericProperty, StringProperty


class LevelTank(MDBoxLayout):
    level = NumericProperty(-1000000000)
    level_stop = NumericProperty(-1000000000)
    rate = NumericProperty(-1000000000)
    rate_formated = StringProperty("")

    def on_rate(self, instance, value):
        litter_per_min = value / 1000
        self.rate_formated = f"{litter_per_min:.2f}"