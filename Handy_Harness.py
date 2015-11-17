import sublime, sublime_plugin, sys

class HandyHarnessCommand(sublime_plugin.TextCommand):
	def run(self, edit, **args):
		
		print "Program start"	

		if args['op'] == 'move_line_to_bottom':
			self.moveLineTo(edit, "bottom")

		if args['op'] == 'move_line_to_top':
			self.moveLineTo(edit, "top")

		if args['op'] == 'move_line_to_next':
			self.moveLineTo(edit, "next")

		if args['op'] == 'move_line_to_prev':
			self.moveLineTo(edit, "prev")


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

		if dest == "next":
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

		if dest == "prev":
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

						




