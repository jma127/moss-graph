#!/usr/bin/env python
# This is an extremely hacky script -- don't judge :(

from HTMLParser import HTMLParser
import os
import sys
import re
import urllib2

class Edge:
    def __init__ (self):
        self.weight = 0.0
        self.nodes = []

class MossParser(HTMLParser):
    match_regex = re.compile(r'match(\d+)\.')
    data_regex = re.compile(r'^(.+)\((\d+)%\)$')

    def __init__(self):
        HTMLParser.__init__(self)
        self.on = False
        self.cur = 0
        self.edges = {}
        self.frequencies = {}

    def handle_starttag(self, tag, attrs):
        attrdict = {attr[0].lower() : attr[1] for attr in attrs}
        if tag.lower() == 'a':
            link = attrdict.get('href', '')
            match = MossParser.match_regex.search(link)
            if match:
                self.on = True
                self.cur = int(match.group(1))

    def handle_data(self, data):
        if self.on:
            parsed = MossParser.data_regex.match(data)
            if parsed:
                name = parsed.group(1).strip()
                if name not in self.frequencies:
                    self.frequencies[name] = 0
                self.frequencies[name] += 1
                similarity = float(parsed.group(2))
                edge = self.edges.setdefault(self.cur, Edge())
                edge.weight += similarity
                edge.nodes.append(name)

    def handle_endtag(self, tag):
        if self.on and tag.lower() == 'a':
            self.on = False

def get_component(node, matrix, used):
    if node in used:
        return []
    used.add(node)
    comp = [node]
    for node2 in matrix[node]:
        comp += get_component(node2, matrix, used)
    return comp

def main():
    if len(sys.argv) < 3: # We should probably use argparse, but w/e
        print '\n'.join([
            'Usage: python moss-graph.py <mossurl> <graphfile>',
            'mossurl: url of the moss results',
            'graphfile: the file in which to output the gephi-formatted graph matrix',
        ''])
        sys.exit(1)

    content = urllib2.urlopen(sys.argv[1] if sys.argv[1].startswith('http') else 'http://' + sys.argv[1]).read()
    parser = MossParser()
    parser.feed(content)

    print 'Summary for MOSS report', sys.argv[1]
    print

    print 'Student frequencies'
    sorted_frequencies = list(parser.frequencies.items())
    sorted_frequencies.sort(key=lambda elem: elem[1], reverse=True)
    for key, val in sorted_frequencies:
        print '{:>41s}{:>9d}'.format(key, val)

    matrix = {}
    for edgeid, edge in parser.edges.iteritems():
        a, b = edge.nodes[0], edge.nodes[1]
        matrix.setdefault(a, {}).setdefault(b, edge.weight / 2.0)
        matrix.setdefault(b, {}).setdefault(a, edge.weight / 2.0)
    nodes = list(matrix.keys())

    with open(sys.argv[2], 'wb') as outfile:
        for node in nodes:
            outfile.write(';"' + node + '"')
        outfile.write('\n')
        for node1 in nodes:
            outfile.write('"' + node1 + '"')
            for node2 in nodes:
                outfile.write(';{}'.format(matrix[node1].get(node2, 0)))
            outfile.write('\n')

    comps = []
    used = set()
    for node in nodes:
        comp = get_component(node, matrix, used)
        if comp:
            comps.append(comp)
    comps.sort(key=lambda comp:len(comp), reverse=True)

    print
    print 'Components'
    for comp in comps:
        sorted_comp = [(node, sum(matrix[node][node2] for node2 in matrix[node]) / (len(comp) - 1)) for node in comp]
        sorted_comp.sort(key=lambda node: node[1], reverse=True)
        print 'Size {:>4d} ========================================'.format(len(sorted_comp))
        for node, deg in sorted_comp:
            print '{:>41s}{:>9.2f}'.format(node, deg)

if __name__ == '__main__':
    main()

