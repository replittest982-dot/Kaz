from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class MineKeyboards:
    
    @staticmethod
    def get_field(mines_open=None):
        """
        Генерирует поле 5x5.
        mines_open: список или строка уже открытых ячеек (из базы), чтобы пометить их.
        """
        keyboard = InlineKeyboardMarkup(row_width=5)
        
        # Ряды A, B, C, D, E
        rows = ['A', 'B', 'C', 'D', 'E']
        buttons = []
        
        for row in rows:
            for col in range(1, 6): # 1, 2, 3, 4, 5
                # Формируем callback, например "mines:A1"
                cb_data = f"mines:{row}{col}"
                
                # Текст кнопки. Можно добавить логику: если ячейка открыта - менять текст.
                # Пока ставим дефолтную 'бомбу' или 'квадрат', как в твоем конфиге ожидается.
                # Обычно это невидимый символ или смайл закрытой коробки.
                text = "🟦" 
                
                # Если у тебя есть список открытых ячеек, можно менять текст тут
                # if mines_open and cb_data in mines_open:
                #     text = "💎" # Или то, что выпало
                
                buttons.append(InlineKeyboardButton(text=text, callback_data=cb_data))
        
        # Добавляем все кнопки поля разом (5 в ряд благодаря row_width=5)
        keyboard.add(*buttons)
        
        # Кнопка "Забрать выигрыш" внизу
        keyboard.row(InlineKeyboardButton("💰 Забрать деньги", callback_data="mines:take_money"))
        
        return keyboard

    @staticmethod
    def bet_menu():
        """
        Клавиатура выбора количества мин
        """
        keyboard = InlineKeyboardMarkup(row_width=3)
        # Добавляем кнопки с количеством мин (как в твоем конфиге mine_cof)
        # Самые популярные варианты
        btns = [
            InlineKeyboardButton("💣 3", callback_data="mines_set:3"),
            InlineKeyboardButton("💣 5", callback_data="mines_set:5"),
            InlineKeyboardButton("💣 10", callback_data="mines_set:10"),
            InlineKeyboardButton("💣 24", callback_data="mines_set:24"),
        ]
        keyboard.add(*btns)
        keyboard.row(InlineKeyboardButton("↩️ В меню", callback_data="back_to_menu"))
        return keyboard

    @staticmethod
    def play_menu():
        """
        Кнопка 'Играть' или 'Сделать ставку'
        """
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🎮 Играть", callback_data="mines_game_start"))
        return keyboard
