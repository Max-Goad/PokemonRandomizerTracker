import gzip
import re as regex

def getLatestFileFrom(directory_path, glob_filter='*.log'):
    """Gets the latest file from the directory specified.

    Latest is specified by name, not creation date.

    TODO: Should use either creation or modification date instead of name.
    """
    file_matches = list(directory_path.glob(glob_filter))
    file_matches.sort(reverse=True)
    if len(file_matches) == 0: raise Exception(f"No files matching glob filter {glob_filter} could be found in directory {directory_path.name}")
    return str(file_matches[0])

def getLinesFromFile(file, custom_strip_fn=lambda x: x):
    """Returns the file as a list of strings (lines).

    Can read from either regular or gzipped files.

    Can specify a function (custom_strip_fn) to run
    on each line while building the list.
    """
    if '.gz' in file.suffixes:
        open_fn = lambda x: gzip.open(x,'rt')
    else:
        open_fn = lambda x: open(x,'r')

    with open_fn(file) as f:
        return [custom_strip_fn(line) for line in f]

def getGroups(pattern, line):
    """Gets regex groups listed in pattern from line (as a tuple).

    If only one group found, returns value (not tuple).

    If no groups are found, returns None.
    """
    groups = None
    match = regex.search(pattern, line)
    if match:
        groups = match.groups()
        if len(groups) == 1:
            groups = groups[0]
    return groups

def stripBracketBlocks(line):
    """A common function that can be used in lambdas to get rid of
    the [Something] blocks commonly found at the beginning of logs

    Also strips leading/trailing spaces/tabs/newlines.
    """
    return regex.sub(r'\[[\w:]+\]', "", line).strip(' \t\n')

class RegexNotFoundError(Exception):
    """ Exception raised when the LogParser can't find a specified regex string """
    pass

class InvalidFormatError(Exception):
    """ Exception raised when the file passed to the file parser is not in a valid format """
    pass

class StringParser:
    """A class meant to ease the process of searching
    programmatically through a list of strings "line-by-line".

    Keeps an internal "current line marker" to help you
    progress through the lines, can extract regex groups
    from a line match, and can even return entire sections
    specified by a start and end regex.
    """

    def __init__(self, lines):
        self.lines = lines
        self.current_line = -1

    def reset(self):
        """Sets the current line marker back to the
        beginning of the list.
        """
        self.current_line = -1

    def moveAndGetGroups(self, regex_str, end_regex=None):
        """Helper function that finds a specified regex_str,
        moves the internal current line marker to that line,
        and returns the capture groups specified in the regex.

        Can specify an end_regex to tell the function when to
        stop looking for the regex_str; By default it searches
        until the end of the file.

        Throws RegexNotFoundError if regex_str not found.
        """
        index = self.current_line + 1
        while index < len(self.lines):

            if end_regex and regex.search(end_regex, self.lines[index]):
                raise RegexNotFoundError

            groups = getGroups(regex_str, self.lines[index])
            #print(f"index = {index}, len = {len(self.lines)}, groups = {groups}")
            if groups is not None:
                self.current_line = index
                return groups
            index += 1
        raise RegexNotFoundError

    def consumeUntil(self, regex_str):
        """Helper function that consumes, collects, and returns all lines following
        the current index until the first line that matches the regex_str.

        Does not change internal current line marker.

        Throws RegexNotFoundError if end of file reached (no matches found).
        """
        index = self.current_line + 1
        consumed_lines = []
        while index < len(self.lines):
            if regex.search(regex_str, self.lines[index]):
                return consumed_lines
            consumed_lines.append(self.lines[index])
            index += 1
        raise RegexNotFoundError

    def consumeRemaining(self):
        """Helper function that consumes, collects, and returns all lines
        following the current line until the end of the file.

        Does not change internal current line marker.
        """
        return self.lines[self.current_line+1:]

    def extractSection(self, begin_regex, end_regex):
        """Helper function that extracts all lines from the specified
        begin regex to the specified end_regex.

        Changes internal current line marker to beginning of section.

        Throws RegexNotFoundError if any matches not found.

        """
        self.moveAndGetGroups(begin_regex)
        return self.consumeUntil(end_regex)


    def find(self, *regex_strings):
        """Finds and returns the contents of the first line which
        contains any of the specified 'regex_strings'.

        Throws RegexNotFoundError if no matches found.
        """
        return_line_fn = lambda i, s: self.lines[i] if regex.search(s, self.lines[i]) else None
        return self._findBase(return_line_fn, *regex_strings)

    def findGroups(self, *regex_strings):
        """Finds and returns the regex capture groups
        of the first line which contains any of the
        specified 'regex_strings' as a tuple.

        Throws RegexNotFoundError if no matches found.
        """
        return_groups_fn = lambda i, s: getGroups(s, self.lines[i])
        return self._findBase(return_groups_fn, *regex_strings)

    def findIndex(self, *regex_strings):
        """Finds and returns the index of the first line which
        contains any of the specified 'regex_strings'.

        Throws RegexNotFoundError if no matches found.
        """
        return_index_fn = lambda i, s: i if regex.search(s, self.lines[i]) else None
        return self._findBase(return_index_fn, *regex_strings)

    def _findBase(self, for_each_fn, *regex_strings):
        """The private base function for all find operations.
        """
        index = 0
        while index < len(self.lines):
            for regex_str in regex_strings:
                result = for_each_fn(index, regex_str)
                if result:
                    return result
            index += 1
        raise RegexNotFoundError

class FileParser(StringParser):
    """A wrapper that converts the file's contents into a
    list of strings compatible with StringParser.

    (See doc for StringParser for more information)

    Can optionally take a "custom_strip_fn" to apply to
    each line as it is processed and converted to a string.
    """
    def __init__(self, file, custom_strip_fn=lambda x: x):
        super().__init__(getLinesFromFile(file, custom_strip_fn=custom_strip_fn))
        self.file = file