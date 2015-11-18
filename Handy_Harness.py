import sublime, sublime_plugin, sys
import json

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

		elif args['op'] == 'history':
			self.history()

		elif args['op'] == 'copy':
			self.history()

	def moveLineTo(self, edit, dest):
		s = self.view.sel()[0]

		size = self.view.size()
		start = s.a
		end = s.b

		while(start > 0 and self.view.substr(start - 1) != '\n'):
			start -= 1

		while(end < size and self.view.substr(end) != '\n'):
			end += 1

		#want region from start to end, plus any extra new lines (full_line).  That's still a region, so I substring it and strip leading or trailing newlines, because depending on where you put it I manually add newlines back in
		line = self.view.substr(self.view.full_line(sublime.Region(start,end))).strip()
 
		if dest == "bottom": 
			self.view.sel().clear()
			self.view.sel().add(sublime.Region(end + 1 + s.a - start))
			self.view.erase(edit, self.view.full_line(sublime.Region(start,end)))
			
			self.view.insert(edit, self.view.size(), "\n" + line)

		if dest == "top":
			self.view.sel().clear()
			self.view.sel().add(sublime.Region(end + 1 + s.a - start))
			self.view.erase(edit, self.view.full_line(sublime.Region(start,end)))
			
			self.view.insert(edit, 0, line + "\n")			

		if dest == "next_bookmark":
			bookmarks = self.view.get_regions('bookmarks')
			if len(bookmarks) != 0:
				index = self.view.sel()[0].a - 1
				while index < self.view.sel()[0].a and len(bookmarks) >= 1:
					index = bookmarks[0].a
					bookmarks.pop(0)

				self.view.insert(edit, index, "\n" +  line)

				self.view.sel().clear()
				self.view.sel().add(sublime.Region(end + 1 + s.a - start))
				self.view.erase(edit, self.view.full_line(sublime.Region(start,end)))

		if dest == "prev_bookmark":
			bookmarks = self.view.get_regions('bookmarks')
			if len(bookmarks) != 0:
				index = self.view.sel()[0].a + 1
				while index > self.view.sel()[0].a and len(bookmarks) >= 1:
					index = bookmarks[len(bookmarks) - 1].a
					bookmarks.pop(len(bookmarks) - 1)

				#must remove line before inserting because insertion will change deletion points
				self.view.sel().clear()
				self.view.sel().add(sublime.Region(end + 1 + s.a - start))
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
			self.view.sel().add(sublime.Region(end + 1 + s.a - start))
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
			self.view.sel().add(sublime.Region(end + 1 + s.a - start))
			self.view.erase(edit, self.view.full_line(sublime.Region(start,end)))

			#needed to determine insert point by combining characters leading up to next empty line, and since we split on newlines, I had to include that in the counting as well
			self.view.insert(edit, start - count - index, line + "\n")


	def eraseLine(self, edit):
		s = self.view.sel()[0]

		size = self.view.size()
		start = s.a
		end = s.b

		while(start > 0 and self.view.substr(start - 1) != '\n'):
			start -= 1

		while(end < size and self.view.substr(end) != '\n'):
			end += 1

		print self.view.substr(self.view.full_line(sublime.Region(start,end))).strip()

		self.view.sel().clear()
		self.view.sel().add(sublime.Region(end + 1 + s.a - start))

		self.view.erase(edit, self.view.full_line(sublime.Region(start,end)))
	

	def history(self):

		self.view.run_command('copy')
		
		with open(sublime.packages_path() + '\handy-harness\Context.sublime-menu') as contextMenu:
			menuData = json.load(contextMenu)

		for item in menuData:
			if 'caption' not in item:
				continue
			if item['caption'] == "History":
				historyItem = item
				break

		#if number of children are less than 5, just append child
		if len(historyItem['children']) < 5:
			#STUB need to add paste command that does set_clipboard then runs paste
			historyItem['children'].append({"caption": sublime.get_clipboard(), "command": "paste", "args": sublime.get_clipboard()})
		else:
			#if number of children equal five, slide 2-5 up, then set 5 to new entry
			#can do this with arr[::] notation
			i = 1
			while i <= 5 - 1:
				historyItem['children'][i-1] = historyItem['children'][i]
				i+=1
			historyItem['children'].pop(5 - 1)
			historyItem['children'].append({"caption": sublime.get_clipboard(), "command": "paste", "args": sublime.get_clipboard()})

		with open(sublime.packages_path() + '\handy-harness\Context.sublime-menu', 'w') as contextMenu:
			menuData[menuData.index(item)] = historyItem
			json.dump(menuData, contextMenu)

#subsets = sublime.load_settings('Preferences.sublime-settings')

#with open(sublime.packages_path().replace('\\','/') + '/My Snippets/Default.sublime-keymap', 'w') as kfyl:
#		kfyl.write(strFile)
#111111122222333333344444455555566666ntext.subntext.sub

