import sublime, sublime_plugin, sys
import json
import random, os
from time import gmtime, strftime
from datetime import date, timedelta

class HandyHarnessCommand(sublime_plugin.TextCommand):

	def run(self, edit, **args):
		
		print "Program start"	

		if args['op'] == 'move_line_to_bottom':
			self.moveLineTo(edit, "bottom")

		elif args['op'] == 'move_line_to_top':
			self.moveLineTo(edit, "top")

		elif args['op'] == 'move_line_to_next_bookmark':
			self.moveLineTo(edit, "next_bookmark")

		elif args['op'] == 'move_line_to_prev_bookmark':
			self.moveLineTo(edit, "prev_bookmark")

		elif args['op'] == 'move_line_to_next_empty':
			self.moveLineTo(edit, "next_empty")

		elif args['op'] == 'move_line_to_prev_empty':
			self.moveLineTo(edit, "prev_empty")

		elif args['op'] == 'erase_line':
			self.eraseLine(edit)

		elif args['op'] == 'history_copy':
			self.historyCopy()
			pass

		elif args['op'] == 'history_paste':
			print args['text']
			if args['text'] == "":
				print "pasting normally"
				self.view.run_command('paste')
			else:
				print "pasting from context menu"
				self.historyPaste(edit, args['text'])

		elif args['op'] == 'random':
			self.randomize(edit)

		elif args['op'] == 'updateReminders':
			self.updateReminders(edit)

		elif args['op'] == 'addToReminders':
			self.addToReminders(edit)

	def moveLineTo(self, edit, dest):
		s = self.view.sel()[0]

		size = self.view.size()
		start = s.begin()
		end = s.end()

		while(start > 0 and self.view.substr(start - 1) != '\n'):
			start -= 1

		while(end < size and self.view.substr(end) != '\n'):
			end += 1

		#want region from start to end, plus any extra new lines (full_line).  That's still a region, so I substring it and strip leading or trailing newlines, because depending on where you put it I manually add newlines back in
		line = self.view.substr(self.view.full_line(sublime.Region(start,end))).strip()
 
		if dest == "bottom": 
			self.view.sel().clear()
			self.view.sel().add(sublime.Region(end + 1 + s.begin() - start))
			self.view.erase(edit, self.view.full_line(sublime.Region(start,end)))
			
			self.view.insert(edit, self.view.size(), "\n" + line)

		if dest == "top":
			self.view.sel().clear()
			self.view.sel().add(sublime.Region(end + 1 + s.begin() - start))
			self.view.erase(edit, self.view.full_line(sublime.Region(start,end)))
			
			self.view.insert(edit, 0, line + "\n")			

		if dest == "next_bookmark":
			bookmarks = self.view.get_regions('bookmarks')
			if len(bookmarks) != 0:
				index = self.view.sel()[0].begin() - 1
				while index < self.view.sel()[0].begin() and len(bookmarks) >= 1:
					index = bookmarks[0].begin()
					bookmarks.pop(0)

				self.view.insert(edit, index, "\n" +  line)

				self.view.sel().clear()
				self.view.sel().add(sublime.Region(end + 1 + s.begin() - start))
				self.view.erase(edit, self.view.full_line(sublime.Region(start,end)))

		if dest == "prev_bookmark":
			bookmarks = self.view.get_regions('bookmarks')
			if len(bookmarks) != 0:
				index = self.view.sel()[0].begin() + 1
				while index > self.view.sel()[0].begin() and len(bookmarks) >= 1:
					index = bookmarks[len(bookmarks) - 1].begin()
					bookmarks.pop(len(bookmarks) - 1)

				#must remove line before inserting because insertion will change deletion points
				self.view.sel().clear()
				self.view.sel().add(sublime.Region(end + 1 + s.begin() - start))
				self.view.erase(edit, self.view.full_line(sublime.Region(start,end)))

				self.view.insert(edit, index, "\n" +  line)

		if dest == "next_empty":
			lines = self.view.substr(sublime.Region(end + 1, size))

			splitLines = lines.split("\n")

			count = 0
			index = 0

			while index < len(splitLines) and splitLines[index] != "":
				count += len(splitLines[index])
				index += 1

			#needed to determine insert point by combining characters leading up to next empty line, and since we split on newlines, I had to include that in the counting as well
			self.view.insert(edit, end + count + index, "\n" +  line)

			self.view.sel().clear()
			self.view.sel().add(sublime.Region(end + 1 + s.begin() - start))
			self.view.erase(edit, self.view.full_line(sublime.Region(start,end)))

		if dest == "prev_empty":
			lines = self.view.substr(sublime.Region(0, start - 1))

			splitLines = lines.split("\n")
			splitLines.reverse()

			count = 0
			index = 0

			while index < len(splitLines) and splitLines[index] != "":
				count += len(splitLines[index])
				index += 1

			self.view.sel().clear()
			self.view.sel().add(sublime.Region(end + 1 + s.begin() - start))
			self.view.erase(edit, self.view.full_line(sublime.Region(start,end)))

			#needed to determine insert point by combining characters leading up to next empty line, and since we split on newlines, I had to include that in the counting as well
			self.view.insert(edit, start - count - index, line + "\n")


	def eraseLine(self, edit):
		s = self.view.sel()[0]

		size = self.view.size()
		start = s.begin()
		end = s.end()

		while(start > 0 and self.view.substr(start - 1) != '\n'):
			start -= 1

		while(end < size and self.view.substr(end) != '\n'):
			end += 1

		print self.view.substr(self.view.full_line(sublime.Region(start,end))).strip()

		self.view.sel().clear()
		self.view.sel().add(sublime.Region(end + 1 + s.begin() - start))

		self.view.erase(edit, self.view.full_line(sublime.Region(start,end)))
	

	def historyCopy(self):

		self.view.run_command('copy')

		try:
			with open(sublime.packages_path() + '\handy-harness\Context.sublime-menu') as contextMenu:
				menuData = json.load(contextMenu)
			valid = True
		except IOError:
			valid = False
			print "Could not open Context File"

		if valid:
			for item in menuData:
				if 'caption' not in item:
					continue
				if item['caption'] == "History":
					historyItem = item
					break

			#if number of children are less than 5, just append child
			if len(historyItem['children']) < 5:
				historyItem['children'].append({"caption": sublime.get_clipboard(), "command": "handy_harness", "args": { "op": "history_paste", "text": sublime.get_clipboard()}})
			else:
				#if number of children equal five, slide 2-5 up, then set 5 to new entry
				#can do this with arr[::] notation
				i = 1
				while i <= 5 - 1:
					historyItem['children'][i-1] = historyItem['children'][i]
					i+=1
				historyItem['children'].pop(5 - 1)
				historyItem['children'].append({"caption": sublime.get_clipboard(), "command": "handy_harness", "args": { "op": "history_paste", "text": sublime.get_clipboard()}})

			with open(sublime.packages_path() + '\handy-harness\Context.sublime-menu', 'w') as contextMenu:
				menuData[menuData.index(item)] = historyItem
				json.dump(menuData, contextMenu)


	def historyPaste(self, edit, text):
		sublime.set_clipboard(text)

		self.view.erase(edit, sublime.Region(self.view.sel()[0].begin(), self.view.sel()[0].end()))
		self.view.insert(edit, self.view.sel()[0].begin(), text)
		
		#normal paste doesn't work here, not sure why
		#sublime.run_command('paste')


	def randomize(self, edit):
		s = self.view.sel()[0]

		size = self.view.size()
		start = s.a
		end = s.b

		while(start > 0 and self.view.substr(start - 1) != '\n'):
			start -= 1

		while(end < size and self.view.substr(end) != '\n'):
			end += 1

		line = self.view.substr(self.view.full_line(sublime.Region(start,end))).strip().split()
		
		lineList = []
		for item in line:
			lineList.append(item)

		random.shuffle(lineList)

		output = ""
		for i, piece in enumerate(lineList):
			output += piece
			if i != len(lineList) - 1:
				output += os.linesep

		print output.encode('ascii', 'ignore')
		print start
		print end

		self.view.insert(edit, end, output.encode('ascii', 'ignore'))
		self.view.erase(edit, self.view.full_line(sublime.Region(start,end)))


	def updateReminders(self, edit):

		print "Starting Remind"

		config = sublime.load_settings("Handy_Harness.sublime-settings")
		
		remindFilePath = config.get("remindFile").encode('ascii','ignore').encode('string-escape')
		insertionFilePath = config.get("todoInsertionFile").encode('ascii','ignore').encode('string-escape')
		startDelim = config.get("startDelimiter").encode('ascii','ignore')
		endDelim = config.get("endDelimiter").encode('ascii','ignore')
		dayLimit = config.get("daysFromNow").encode('ascii','ignore')

		if type(remindFilePath) is None or type(insertionFilePath) is None or type(dayLimit) is None:
			print "Missing Some Settings, Check remindFilePath, insertionFilePath, or dayLimit settings"
			return 

		try:
			f = open(remindFilePath, 'r')
			valid = True
			pass
		except ValueError, IOError:
			valid = False
			print "Cannot open reminder file"

		print "Loaded Reminder File"

		if(valid):
			reminders = f.read().split('\n')
			f.close()

			reminders.sort()

			#Find string of today + dayLimit in "YE-MO-DA" form
			today = date.today()
			endDay = today + timedelta(int(dayLimit))
			endDate = strftime("%Y-%m-%d", endDay.timetuple())

			#print reminders[0]
			#print reminders[0][:10]

			i = 0
			results = ""
			#Loop through sorted list until you run out or until you find a date later than the end date
			while i < len(reminders) and reminders[i][:10] < endDate:
				results += reminders[i]
				results += '\n'
				i+=1

			if not results:
				results = "No reminders within " + endDate + " days\n"

			#Pick up destination File
			try:
				f = open(insertionFilePath.encode('ascii','ignore').encode('string-escape'), 'r')
				valid = True
				pass
			except ValueError, IOError:
				valid = False
				print "Cannot open insertion file"

			print "Loaded Insertion File"

			#Parse through and remove all between start delimiter and end delimiter
			#....also add cases for Start of File and End of File SOF/EOF
			#....also add cases for line numbers of destination file? or relative numbers?
			insert = f.read().encode('ascii','ignore')
			f.close()
			#print insert

			start = -1
			end = -1
			if startDelim == "sof" or startDelim == "SOF":
				print "Start of File found"
				start = 0
			elif startDelim == "eof" or startDelim == "EOF":
				print "Found Improper startDelim"
				return
			else:
				print "Finding Start Delimiter from String"
				start = insert.find(startDelim) + len(startDelim)

			if endDelim == "eof" or endDelim == "eof":
				print "End of File found"
				end = len(insert)
			elif endDelim == "sof" or endDelim == "SOF":
				print "Found Improper endDelim"
				return
			else:
				print "Finding End Delimiter from String"
				end = insert.find(endDelim)
			
			if start == -1 or end == -1:
				print "Could not find startDelim or endDelim in insertion file"
				return

			#print start
			#print end

			if start != end:
				self.view.erase(edit, sublime.Region(start,end))

			#Insert results into that space
			self.view.insert(edit, start, '\n' +  results)


	def addToReminders(self, edit):
		#grab line

		#check if it is a valid reminder, if not, stop

		#open reminders file with write permissions

		#append to reminders file

		#save reminders file?

		#if successful, remove from current file

		pass


	def removeFromReminders(self,edit):
		##STUB, archive instead of remove?

		#grab line

		#open reminders file with write permissions

		#search for line

		#erase line from reminders

		#Close/save reminders file

		#if successful, remove line from current file

		pass


	def goToReminders(self,edit):
		#open up a new tab with reminders file

		#shift focus to new tab

		pass