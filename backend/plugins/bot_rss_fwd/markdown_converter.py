from bs4.element import NavigableString, Tag
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Union
from enum import Enum
import re

class NodeType(Enum):
    EMPTY = 0
    TEXT = 1
    A = 2
    IMAGE = 3
    LINE_BREAK = 4
    H1 = 5
    H2 = 6
    H3 = 7

@dataclass
class MarkdownNode:
    content: str
    url: str = ''
    strong: bool = False
    italic: bool = False
    type: NodeType = NodeType.EMPTY
    def __str__(self):
        match self.type:
            case NodeType.EMPTY:
                return ''
            case NodeType.TEXT:
                if self.strong and self.italic:
                    return f' ***{self.content}*** '
                elif self.strong:
                    return f' **{self.content}** '
                elif self.italic:
                    return f' *{self.content}* '
                return self.content
            case NodeType.A:
                return f'[{self.content}]({self.url})'
            case NodeType.IMAGE:
                return f'![{self.content}]({self.url})'
            case NodeType.LINE_BREAK:
                return '\n'
            case NodeType.H1:
                return f'# {self.content}'
            case NodeType.H2:
                return f'## {self.content}'
            case NodeType.H3:
                return f'### {self.content}'

def _convert_block_element_children_to_mdnode(element: Tag) -> list[MarkdownNode]:
    nodes = []
    last_element_inline = False
    for elem in element.children:
        if elem.name in ('html', 'body', '[document]'):
            nodes.extend(_convert_block_element_children_to_mdnode(elem))
        elif elem.name in ('h1', 'h2', 'h3'):
            nodes.extend(_convert_block_element_to_mdnode(elem))
        elif elem.name in ('p', 'div'):
            # handle block level elements
            if last_element_inline:
                nodes.append(MarkdownNode('', type=NodeType.LINE_BREAK))
                last_element_inline = False
            nodes.extend(_convert_block_element_to_mdnode(elem))
            nodes.append(MarkdownNode('', type=NodeType.LINE_BREAK))
        elif elem.name == 'br':
            nodes.append(MarkdownNode('', type=NodeType.LINE_BREAK))
            last_element_inline = False
        else:
            # handle inline elements
            nodes.extend(_convert_inline_element_to_mdnode(elem))
            last_element_inline = True
    return nodes

def _convert_block_element_to_mdnode(element: Union[Tag, NavigableString]) -> list[MarkdownNode]:
    if isinstance(element, NavigableString):
        return [MarkdownNode(element.strip(), type=NodeType.TEXT)]
    if element.name in ('h1', 'h2', 'h3'):
        # handle headers
        content = _render_inline_element_children_md(element).strip()
        match element.name:
            case 'h1':
                header_node = MarkdownNode(content, type=NodeType.H1)
            case 'h2':
                header_node = MarkdownNode(content, type=NodeType.H2)
            case 'h3':
                header_node = MarkdownNode(content, type=NodeType.H3)
        return [header_node, MarkdownNode('', type=NodeType.LINE_BREAK)]
    return _convert_block_element_children_to_mdnode(element)

def _convert_inline_element_children_to_mdnode(element: Tag, strong=False, italic=False) -> list[MarkdownNode]:
    nodes = []
    for elem in element.children:
        nodes.extend(_convert_inline_element_to_mdnode(elem, strong, italic))
        # match elem.name:
        #     case 'a':
        #         text = _render_inline_element_md(elem, strong, italic)
        #         if text:
        #             nodes.append(MarkdownNode(text, elem['href'], type=NodeType.A))
        #     case 'strong':
        #         nodes.extend(_convert_inline_element_to_mdnode(elem, True, italic))
        #     case 'em':
        #         nodes.extend(_convert_inline_element_to_mdnode(elem, strong, True))
        #     case 'img':
        #         nodes.append(MarkdownNode(elem['alt'], elem['src'], type=NodeType.IMAGE))
        #     case _:
        #         nodes.extend(_convert_inline_element_to_mdnode(elem, strong, italic))
    return nodes

def _convert_inline_element_to_mdnode(element: Union[Tag, NavigableString], strong=False, italic=False) -> list[MarkdownNode]:
    if isinstance(element, NavigableString):
        return [MarkdownNode(element.strip(), strong=strong, italic=italic, type=NodeType.TEXT)]
    match element.name:
        case 'a':
            text = _render_inline_element_children_md(element, strong, italic).strip()
            href = element.attrs.get('href', '')
            if text:
                return [MarkdownNode(text, href, type=NodeType.A)]
        case 'img':
            return [MarkdownNode(element.attrs.get('alt', ''), element.attrs.get('src', ''), type=NodeType.IMAGE)]
        case 'strong':
            return _convert_inline_element_children_to_mdnode(element, True, italic)
        case 'em':
            return _convert_inline_element_children_to_mdnode(element, strong, True)
        case _:
            return _convert_inline_element_children_to_mdnode(element, strong, italic)
    # if element.name == 'strong':
    #     strong = True
    # elif element.name == 'em':
    #     italic = True
    # return _convert_inline_element_children_to_mdnode(element, strong, italic)
    
def _merge_neighbour_nodes(nodes: list[MarkdownNode]) -> list[MarkdownNode]:
    last_node = MarkdownNode('', type=NodeType.EMPTY)
    new_nodes = []
    for current_node in nodes:
        if current_node.type == NodeType.TEXT and last_node.type == NodeType.TEXT and\
            last_node.strong == current_node.strong and last_node.italic == current_node.italic:
            # merge neighbour text nodes with same style
            last_node.content += current_node.content
        else:
            if last_node.type != NodeType.EMPTY:
                new_nodes.append(last_node)
            last_node = current_node
    if last_node.type != NodeType.EMPTY:
        new_nodes.append(last_node)
    return new_nodes

def _render_inline_element_children_md(element, strong=False, italic=False) -> str:
    nodes = _merge_neighbour_nodes(_convert_inline_element_children_to_mdnode(element, strong, italic))
    return ''.join(map(str, nodes))

def _render_inline_element_md(element, strong=False, italic=False) -> str:
    nodes = _merge_neighbour_nodes(_convert_inline_element_to_mdnode(element, strong, italic))
    return ''.join(map(str, nodes))

def _render_block_element_md(element) -> str:
    nodes = _merge_neighbour_nodes(_convert_block_element_to_mdnode(element))
    return ''.join(map(str, nodes))

def _fix_url_in_text_node(nodes: list[MarkdownNode]) -> list[MarkdownNode]:
    for node in nodes:
        if node.type == NodeType.TEXT:
            # [\x21-\x7E]: ASCII printable characters
            # [^\x00-\x7F]: non-ASCII characters
            pattern = re.compile(r'(https?://[\x21-\x7E]+)([^\x00-\x7F])')
            node.content = pattern.sub(r'\1 \2', node.content)
    return nodes

def render_md(element) -> str:
    nodes = _merge_neighbour_nodes(_convert_block_element_to_mdnode(element))
    nodes = _fix_url_in_text_node(nodes)
    return ''.join(map(str, nodes))