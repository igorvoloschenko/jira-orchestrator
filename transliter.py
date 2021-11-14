class Transliter():
    def __init__(self, mapping={}):
        self.mapping: dict
        
        if not mapping:
            default_pre_processor_mapping = {
                "х": "kh",
                "ц": "ts",                
                "ж": "zh",
                "ч": "ch",
                "ш": "sh",
                "щ": "shch",
                "ь": "",
                "ъ": "",
                "ю": "ju",
                "я": "ja",
                "Х": "Kh",
                "Ц": "Ts",                
                "Ж": "Zh",
                "Ч": "Ch",
                "Ш": "Sh",
                "Щ": "Shch",
                "Ь": "",
                "Ъ": "",
                "Ю": "Ju",
                "Я": "Ja",
            }

            default_mapping = (
                "абвгдезийклмнопрстуфыэАБВГДЕЗИЙКЛМНОПРСТУФЫЭ",
                "abvgdezijklmnoprstufyeABVGDEZIJKLMNOPRSTUFYE",
            )
            mapping = default_pre_processor_mapping.copy()
            mapping.update({a:b for a, b in zip(*default_mapping)})
        self.setMapping(mapping)
    
    def setMapping(self, mapping):
        self.mapping = {ord(a):b for a, b in mapping.items()}

    def translate(self, s: str):
        return s.translate(self.mapping)