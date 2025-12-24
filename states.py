from aiogram.dispatcher.filters.state import StatesGroup, State

class admin_states(StatesGroup):
    change_invoice = State()
    popol_cb = State()

class broadcast(StatesGroup):
    start = State()

class ban(StatesGroup):
    start = State()

class unban(StatesGroup):
    start = State()

class OtherGameState(StatesGroup):
    bet_amount = State()


class BlackjackGameState(StatesGroup):
    bet_amount = State()


class SlotsGameState(StatesGroup):
    bet_amount = State()


class AdminSearchUserState(StatesGroup):
    user_id = State()


class DepositQiwiState(StatesGroup):
    amount = State()


class BakkaraGameState(StatesGroup):
    bet_amount = State()


class OutputState(StatesGroup):
    amount = State()
    place = State()
    requesites = State()
    confirm = State()


class JackpotGameState(StatesGroup):
    bet_amount = State()


class AdminChangeBalance(StatesGroup):
    amount = State()
    confitm = State()


class AdminChangeComission(StatesGroup):
    percent = State()
    confitm = State()


class AdminPictureMailing(StatesGroup):
    text = State()
    picture = State()
    confirm = State()


class AdminWithoutPictureMailing(StatesGroup):
    text = State()
    confirm = State()


class balance_states(StatesGroup):
    BS1 = State()
    BS2 = State()
    
    
class MinesStorage(StatesGroup):
    get_mines = State()
    bet = State()
    start = State()
    game = State()

class surprise_states(StatesGroup):
    id_amount = State()

class search_ref(StatesGroup):
    start = State()

class change_max(StatesGroup):
    start = State()

class contest1(StatesGroup):
    start = State()

class contest2(StatesGroup):
    start = State()

class empty_cashback(StatesGroup):
    start = State()

class empty_ref(StatesGroup):
    start = State()

class search(StatesGroup):
    start = State()

class add_moder(StatesGroup):
    start = State()

class remove_moder(StatesGroup):
    start = State()

class ban_mod(StatesGroup):
    start = State()

class unban_mod(StatesGroup):
    start = State()