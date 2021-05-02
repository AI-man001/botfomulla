import re, pymongo, json
dbcursor = pymongo.MongoClient().botfomula


class Bot:
  def __init__(self, data):
    self.response = {'type': 'text'}
    self.number = data.get('number')
    self.message = data.get('message')
    self.botmenus = self.bot_menus()

  def bot_menus(self):
    return dbcursor.bot.find_one({'_id': 'all_menu'})

  def updateBot(self):
    new_bot = json.load(open('bot.json'))
    dbcursor.bot.delete_one({'_id': 'all_menu'})
    dbcursor.bot.insert_one(new_bot)
    return {'text': 'Update Successifull'}

  def currentMenu(self):
    current_menu = dbcursor.sessions.find_one({'number': self.number})
    return current_menu.get('current_menu') if current_menu else 'main_menu'

  def getMainMenu(self):
    self.updateCurrentMenu('main_menu')
    return self.generateMenuMessage(self.botmenus.get('main_menu'))

  def processNewMessage(self):
    current_menu = self.currentMenu()
    response = self.botmenus[current_menu].get(self.message, False)
    if response:
      if type(response) == dict:
        _selected = self.botmenus[current_menu][self.message]
        self.response['text'] = _selected[list(response.keys())[0]].get('message')
      elif response.endswith('_menu'):
        self.updateCurrentMenu(response)
        self.response['text'] = self.generateMenuMessage(self.botmenus.get(response))
      elif response.endswith('_now'):
        self.updateCurrentMenu(response)
        self.response['text'] = self.getNextQuestion(current_menu, self.botmenus.get(response))
      else:
        self.response['text'] = response
    elif current_menu:
      if current_menu.endswith('_now'):
        self.response['text'] = self.getNextQuestion(current_menu, self.botmenus.get(current_menu))
      elif self.message == 'menu':
        self.response['text'] = self.getMainMenu()
      else:
        self.response['text'] = self.generateMenuMessage(self.botmenus.get(current_menu))
    else:
      self.response['text'] = self.getMainMenu()
    return self.response

  def getEmojiNumber(self, number):
    key_map = {
        '0': '0️⃣',
        '1': '1️⃣',
        '2': '2️⃣',
        '3': '3️⃣',
        '4': '4️⃣',
        '5': '5️⃣',
        '6': '6️⃣',
        '7': '7️⃣',
        '8': '8️⃣',
        '9': '9️⃣'
    }
    newstring = ''
    for charector in number:
      general_char = f"{newstring}{charector}"
      emoji_number = f"{newstring}{key_map.get(charector)} "
      newstring = emoji_number if charector.isdigit() else general_char
    return newstring

  def updateCurrentMenu(self, menu):
    _filter = {'number': self.number}
    current_session = dbcursor.sessions.find_one(_filter)
    if current_session:
      dbcursor.sessions.update_one(_filter, {'$set': {'current_menu': menu}})
    else:
      dbcursor.sessions.insert_one({'number': self.number, 'stage': 0, 'current_menu': menu})
    return True

  def generateMenuMessage(self, target):
    skip_options = ['title', 'info']
    reply_message = f"{target.get('title')}\n\n"
    for opt_num in target.keys():
      lable = target.get(opt_num)
      if type(lable) == dict:
        lable = lable[list(lable.keys())[0]].get('title')
      if lable.endswith('_menu'):
        option_label = re.sub('_menu', '', lable)
      else:
        option_label = re.sub('_now', ' Now', lable)
      if not opt_num in skip_options:
        option = self.getEmojiNumber(opt_num)
        reply_message += f"{option} {option_label.title()}\n"
    return reply_message

  def fill_in_database(self, collection_name, data):
    item_name = data.get('name')
    current_collection = dbcursor.get_collection(collection_name)
    isregistering = current_collection.find_one({'number': self.number, 'status': 'processing'})
    if isregistering:
      current_collection.update_one({'number': self.number}, {'$set': {item_name: self.message}})
    else:
      current_collection.insert_one({'number': self.number, 'status': 'processing', item_name: self.message})
    return data.get('message')

  def getNextQuestion(self, current_menu, questions):
    _filter = {'number': self.number}
    collection_name = questions.get('collection_name')
    current_qsn = dbcursor.sessions.find_one(_filter).get('stage')
    current_qsn += 1
    questions.pop('collection_name')
    if current_qsn > int(max(questions.keys())):
      current_qsn = 0
      current_menu = re.sub('_now', '', current_menu)
      results = [key for key in self.botmenus.keys() if current_menu in key]
      for result in results:
        if result.endswith('_menu'):
          self.updateCurrentMenu(result)
          dbcursor.sessions.update_one(_filter, {'$set': {'stage': current_qsn}})
          dbcursor.get_collection(collection_name).update_one(_filter, {'$set': {'status': 'pending'}})
          return self.generateMenuMessage(self.botmenus.get(result))
    target = str(current_qsn - 1) if not current_qsn == 1 else '1'
    questions[str(current_qsn)]['name'] = questions[target]['name']
    dbcursor.sessions.update_one(_filter, {'$set': {'stage': current_qsn}})
    return self.fill_in_database(collection_name, questions[str(current_qsn)])


while True:
  option = input("Enter your message here $_ ")
  data = {'number': '+263786854223', 'message': option}
  response = Bot(data).updateBot() if option == 'update' else Bot(data).processNewMessage()
  print(response.get('text'))