# my_tools.py

from agentops import record_tool
from crewai_tools import (
    CodeInterpreterTool as MyCodeInterpreterTool, ScrapeElementFromWebsiteTool, TXTSearchTool, SeleniumScrapingTool,
    PGSearchTool, PDFSearchTool, MDXSearchTool, JSONSearchTool, GithubSearchTool,
    EXASearchTool, DOCXSearchTool, CSVSearchTool, ScrapeWebsiteTool, FileReadTool,
    DirectorySearchTool, DirectoryReadTool, CodeDocsSearchTool, YoutubeVideoSearchTool,
    SerperDevTool, YoutubeChannelSearchTool, WebsiteSearchTool
)
from custom_tools import CustomApiTool, MyCustomFileWriteTool, CustomCodeInterpreterTool
from langchain_community.tools import YahooFinanceNewsTool
import streamlit as st
import os
from core_utils import rnd_id
import json
from datetime import datetime
from base_tool import MyTool

class MyScrapeWebsiteTool(MyTool):
    def __init__(self, tool_id=None, website_url=None):
        parameters = {
            'website_url': {'mandatory': False}
        }
        if website_url:
            parameters['website_url'] = website_url
        super().__init__(tool_id, 'ScrapeWebsiteTool', "A tool that can be used to read website content.", parameters)

    @record_tool('ScrapeWebsiteTool')
    def create_tool(self) -> ScrapeWebsiteTool:
        return ScrapeWebsiteTool(self.parameters.get('website_url') if self.parameters.get('website_url') else None)

class MyFileReadTool(MyTool):
    def __init__(self, tool_id=None, file_path=None):
        parameters = {
            'file_path': {'mandatory': False}
        }
        if file_path:
            parameters['file_path'] = file_path
        super().__init__(tool_id, 'FileReadTool', "A tool that can be used to read a file's content.", parameters)

    @record_tool('FileReadTool')
    def create_tool(self) -> FileReadTool:
        if self.parameters.get('file_path'):
            self.parameters['file_path'] = self._validate_path(self.parameters['file_path'])
        return FileReadTool(self.parameters.get('file_path'))

class MyDirectorySearchTool(MyTool):
    def __init__(self, tool_id=None, directory=None):
        parameters = {
            'directory': {'mandatory': True}
        }
        if directory:
            parameters['directory'] = directory
        super().__init__(
            tool_id, 
            'DirectorySearchTool',
            "A tool that can be used for semantic search queries within a directory's content.",
            parameters
        )
        
        self.workspace_root = os.path.abspath(os.getenv('WORKSPACE_DIR', './workspace'))
        os.makedirs(self.workspace_root, exist_ok=True)

    def _create_directory(self, directory: str) -> str:
        rel_path = os.path.normpath(directory).lstrip('/')
        full_path = os.path.join(self.workspace_root, rel_path)
        abs_path = os.path.abspath(full_path)
        
        if not abs_path.startswith(self.workspace_root):
            raise ValueError("Invalid directory path - must stay within workspace")
            
        os.makedirs(abs_path, exist_ok=True)
        
        return abs_path

    @record_tool('DirectorySearchTool')
    def create_tool(self) -> DirectorySearchTool:
        directory = self.parameters.get('directory')
        if not directory:
            raise ValueError("Directory parameter is required")
        
        try:
            safe_path = self._validate_path(self._create_directory(directory))
            placeholder_path = os.path.join(safe_path, '.gitkeep')
            if not os.path.exists(placeholder_path):
                with open(placeholder_path, 'w') as f:
                    f.write('')
            
            tool = DirectorySearchTool()
            tool.directory = safe_path
            return tool
            
        except Exception as e:
            raise ValueError(f"Failed to initialize directory tool: {str(e)}")
        
class MyDirectoryReadTool(MyTool):
    def __init__(self, tool_id=None, directory_contents=None):
        parameters = {
            'directory_contents': {'mandatory': True}
        }
        if directory_contents:
            parameters['directory_contents'] = directory_contents
        super().__init__(tool_id, 'DirectoryReadTool', "Use the tool to list the contents of the specified directory.", parameters)

    @record_tool('DirectoryReadTool')
    def create_tool(self) -> DirectoryReadTool:
        if self.parameters.get('directory_contents'):
            self.parameters['directory_contents'] = self._validate_path(self.parameters['directory_contents'])
        return DirectoryReadTool(self.parameters.get('directory_contents'))

class MyCodeDocsSearchTool(MyTool):
    def __init__(self, tool_id=None, code_docs=None):
        parameters = {
            'code_docs': {'mandatory': False}
        }
        if code_docs:
            parameters['code_docs'] = code_docs
        super().__init__(tool_id, 'CodeDocsSearchTool', "A tool that can be used to search through code documentation.", parameters)

    @record_tool('CodeDocsSearchTool')
    def create_tool(self) -> CodeDocsSearchTool:
        if self.parameters.get('code_docs'):
            self.parameters['code_docs'] = self._validate_path(self.parameters['code_docs'])
        return CodeDocsSearchTool(self.parameters.get('code_docs'))

class MyYoutubeVideoSearchTool(MyTool):
    def __init__(self, tool_id=None, youtube_video_url=None):
        parameters = {
            'youtube_video_url': {'mandatory': False}
        }
        if youtube_video_url:
            parameters['youtube_video_url'] = youtube_video_url
        super().__init__(tool_id, 'YoutubeVideoSearchTool', "A tool that can be used for semantic search queries within YouTube video content.", parameters)

    @record_tool('YoutubeVideoSearchTool')
    def create_tool(self) -> YoutubeVideoSearchTool:
        return YoutubeVideoSearchTool(self.parameters.get('youtube_video_url'))

class MySerperDevTool(MyTool):
    def __init__(self, tool_id=None, serper_api_key=None):
        parameters = {
            'serper_api_key': {'mandatory': True}
        }
        if serper_api_key:
            parameters['serper_api_key'] = serper_api_key
        super().__init__(tool_id, 'SerperDevTool', "A tool that can be used to search the internet with a search query.", parameters)

    @record_tool('SerperDevTool')
    def create_tool(self) -> SerperDevTool:
        os.environ['SERPER_API_KEY'] = self.parameters.get('serper_api_key')
        return SerperDevTool()

class MyYoutubeChannelSearchTool(MyTool):
    def __init__(self, tool_id=None, youtube_channel_handle=None):
        parameters = {
            'youtube_channel_handle': {'mandatory': False}
        }
        if youtube_channel_handle:
            parameters['youtube_channel_handle'] = youtube_channel_handle
        super().__init__(tool_id, 'YoutubeChannelSearchTool', "A tool that can be used for semantic search queries within YouTube channel content.", parameters)

    @record_tool('YoutubeChannelSearchTool')
    def create_tool(self) -> YoutubeChannelSearchTool:
        return YoutubeChannelSearchTool(self.parameters.get('youtube_channel_handle'))

class MyWebsiteSearchTool(MyTool):
    def __init__(self, tool_id=None, website=None):
        parameters = {
            'website': {'mandatory': False}
        }
        if website:
            parameters['website'] = website
        super().__init__(tool_id, 'WebsiteSearchTool', "A tool that can be used for semantic search queries within specific website content.", parameters)

    @record_tool('WebsiteSearchTool')
    def create_tool(self) -> WebsiteSearchTool:
        return WebsiteSearchTool(self.parameters.get('website'))
   
class MyCSVSearchTool(MyTool):
    def __init__(self, tool_id=None, csv=None):
        parameters = {
            'csv': {'mandatory': False}
        }
        if csv:
            parameters['csv'] = csv
        super().__init__(tool_id, 'CSVSearchTool', "A tool that can be used for semantic search queries within CSV content.", parameters)

    @record_tool('CSVSearchTool')
    def create_tool(self) -> CSVSearchTool:
        if self.parameters.get('csv'):
            self.parameters['csv'] = self._validate_path(self.parameters['csv'])
        return CSVSearchTool(csv=self.parameters.get('csv'))

class MyDocxSearchTool(MyTool):
    def __init__(self, tool_id=None, docx=None):
        parameters = {
            'docx': {'mandatory': False}
        }
        if docx:
            parameters['docx'] = docx
        super().__init__(tool_id, 'DOCXSearchTool', "A tool that can be used for semantic search queries within DOCX content.", parameters)

    @record_tool('DOCXSearchTool')
    def create_tool(self) -> DOCXSearchTool:
        if self.parameters.get('docx'):
            self.parameters['docx'] = self._validate_path(self.parameters['docx'])
        return DOCXSearchTool(docx=self.parameters.get('docx'))
    
class MyEXASearchTool(MyTool):
    def __init__(self, tool_id=None, exa_api_key=None):
        parameters = {
            'exa_api_key': {'mandatory': True}
        }
        if exa_api_key:
            parameters['exa_api_key'] = exa_api_key
        super().__init__(tool_id, 'EXASearchTool', "A tool that can be used to search the internet with a search query.", parameters)

    @record_tool('EXASearchTool')
    def create_tool(self) -> EXASearchTool:
        os.environ['EXA_API_KEY'] = self.parameters.get('exa_api_key')
        return EXASearchTool()

class MyGithubSearchTool(MyTool):
    def __init__(self, tool_id=None, github_repo=None, gh_token=None, content_types=None):
        parameters = {
            'github_repo': {'mandatory': False},
            'gh_token': {'mandatory': True},
            'content_types': {'mandatory': False}
        }
        if github_repo:
            parameters['github_repo'] = github_repo
        if gh_token:
            parameters['gh_token'] = gh_token
        if content_types:
            parameters['content_types'] = content_types
        super().__init__(tool_id, 'GithubSearchTool', "A tool that can be used for semantic search queries within a GitHub repository's content. Valid content_types: code, repo, pr, issue (comma separated)", parameters)

    @record_tool('GithubSearchTool')
    def create_tool(self) -> GithubSearchTool:
        content_types = self.parameters.get('content_types').split(",") if self.parameters.get('content_types') else ["code", "repo", "pr", "issue"]
        return GithubSearchTool(
            github_repo=self.parameters.get('github_repo'),
            gh_token=self.parameters.get('gh_token'),
            content_types=content_types
        )

class MyJSONSearchTool(MyTool):
    def __init__(self, tool_id=None, json_path=None):
        parameters = {
            'json_path': {'mandatory': False}
        }
        if json_path:
            parameters['json_path'] = json_path
        super().__init__(tool_id, 'JSONSearchTool', "A tool that can be used for semantic search queries within JSON content.", parameters)

    @record_tool('JSONSearchTool')
    def create_tool(self) -> JSONSearchTool:
        if self.parameters.get('json_path'):
            self.parameters['json_path'] = self._validate_path(self.parameters['json_path'])
        return JSONSearchTool(json_path=self.parameters.get('json_path'))

class MyMDXSearchTool(MyTool):
    def __init__(self, tool_id=None, mdx=None):
        parameters = {
            'mdx': {'mandatory': False}
        }
        if mdx:
            parameters['mdx'] = mdx
        super().__init__(tool_id, 'MDXSearchTool', "A tool that can be used for semantic search queries within MDX content.", parameters)

    @record_tool('MDXSearchTool')
    def create_tool(self) -> MDXSearchTool:
        if self.parameters.get('mdx'):
            self.parameters['mdx'] = self._validate_path(self.parameters['mdx'])
        return MDXSearchTool(mdx=self.parameters.get('mdx'))
    
class MyPDFSearchTool(MyTool):
    def __init__(self, tool_id=None, pdf=None):
        parameters = {
            'pdf': {'mandatory': False}
        }
        if pdf:
            parameters['pdf'] = pdf
        super().__init__(tool_id, 'PDFSearchTool', "A tool that can be used for semantic search queries within PDF content.", parameters)

    @record_tool('PDFSearchTool')
    def create_tool(self) -> PDFSearchTool:
        if self.parameters.get('pdf'):
            self.parameters['pdf'] = self._validate_path(self.parameters['pdf'])
        return PDFSearchTool(self.parameters.get('pdf'))

class MyPGSearchTool(MyTool):
    def __init__(self, tool_id=None, db_uri=None):
        parameters = {
            'db_uri': {'mandatory': True}
        }
        if db_uri:
            parameters['db_uri'] = db_uri
        super().__init__(tool_id, 'PGSearchTool', "A tool that can be used to search a PostgreSQL database.", parameters)

    @record_tool('PGSearchTool')
    def create_tool(self) -> PGSearchTool:
        return PGSearchTool(self.parameters.get('db_uri'))

class MySeleniumScrapingTool(MyTool):
    def __init__(self, tool_id=None, website_url=None, css_element=None, cookie=None, wait_time=None):
        parameters = {
            'website_url': {'mandatory': False},
            'css_element': {'mandatory': False},
            'cookie': {'mandatory': False},
            'wait_time': {'mandatory': False}
        }
        if website_url:
            parameters['website_url'] = website_url
        if css_element:
            parameters['css_element'] = css_element
        if cookie:
            parameters['cookie'] = cookie
        if wait_time:
            parameters['wait_time'] = wait_time
        super().__init__(
            tool_id, 
            'SeleniumScrapingTool', 
            "A tool that can be used to read specific parts of website content. CSS elements are separated by commas, cookies are in the format {key1:value1},{key2:value2}", 
            parameters
        )

    @record_tool('SeleniumScrapingTool')
    def create_tool(self) -> SeleniumScrapingTool:
        cookie_arrayofdicts = [
            {k.strip(): v.strip()} 
            for item in self.parameters.get('cookie', '').split(',') 
            for k, v in [item.strip('{}').split(':', 1)]
        ] if self.parameters.get('cookie') else None

        return SeleniumScrapingTool(
            website_url=self.parameters.get('website_url'),
            css_element=self.parameters.get('css_element').split(",") if self.parameters.get('css_element') else None,
            cookie=cookie_arrayofdicts,
            wait_time=self.parameters.get('wait_time') if self.parameters.get('wait_time') else 10
        )

class MyTXTSearchTool(MyTool):
    def __init__(self, tool_id=None, txt=None):
        parameters = {
            'txt': {'mandatory': False}
        }
        if txt:
            parameters['txt'] = txt
        super().__init__(tool_id, 'TXTSearchTool', "A tool that can be used for semantic search queries within TXT content.", parameters)

    @record_tool('TXTSearchTool')
    def create_tool(self) -> TXTSearchTool:
        if self.parameters.get('txt'):
            self.parameters['txt'] = self._validate_path(self.parameters['txt'])
        return TXTSearchTool(self.parameters.get('txt'))

class MyScrapeElementFromWebsiteTool(MyTool):
    def __init__(self, tool_id=None, website_url=None, css_element=None, cookie=None):
        parameters = {
            'website_url': {'mandatory': False},
            'css_element': {'mandatory': False},
            'cookie': {'mandatory': False}
        }
        if website_url:
            parameters['website_url'] = website_url
        if css_element:
            parameters['css_element'] = css_element
        if cookie:
            parameters['cookie'] = cookie
        super().__init__(
            tool_id, 
            'ScrapeElementFromWebsiteTool', 
            "A tool that can be used to read specific parts of website content. CSS elements are separated by commas, cookies are in the format {key1:value1},{key2:value2}", 
            parameters
        )

    @record_tool('ScrapeElementFromWebsiteTool')
    def create_tool(self) -> ScrapeElementFromWebsiteTool:
        cookie_arrayofdicts = [
            {k.strip(): v.strip()} 
            for item in self.parameters.get('cookie', '').split(',') 
            for k, v in [item.strip('{}').split(':', 1)]
        ] if self.parameters.get('cookie') else None
        return ScrapeElementFromWebsiteTool(
            website_url=self.parameters.get('website_url'),
            css_element=self.parameters.get('css_element').split(",") if self.parameters.get('css_element') else None,
            cookie=cookie_arrayofdicts
        )
    
class MyYahooFinanceNewsTool(MyTool):
    def __init__(self, tool_id=None):
        parameters = {}
        super().__init__(tool_id, 'YahooFinanceNewsTool', "A tool that can be used to search Yahoo Finance News.", parameters)

    @record_tool('YahooFinanceNewsTool')
    def create_tool(self) -> YahooFinanceNewsTool:
        return YahooFinanceNewsTool()

TOOL_CLASSES = {
    'SerperDevTool': MySerperDevTool,
    'WebsiteSearchTool': MyWebsiteSearchTool,
    'ScrapeWebsiteTool': MyScrapeWebsiteTool,
    'SeleniumScrapingTool': MySeleniumScrapingTool,
    'ScrapeElementFromWebsiteTool': MyScrapeElementFromWebsiteTool,
    'CodeInterpreterTool': MyCodeInterpreterTool,
    'CustomCodeInterpreterTool': CustomCodeInterpreterTool,
    'FileReadTool': MyFileReadTool,
    'CustomFileWriteTool': MyCustomFileWriteTool,
    'DirectorySearchTool': MyDirectorySearchTool,
    'DirectoryReadTool': MyDirectoryReadTool,
    'YoutubeVideoSearchTool': MyYoutubeVideoSearchTool,
    'YoutubeChannelSearchTool': MyYoutubeChannelSearchTool,
    'GithubSearchTool': MyGithubSearchTool,
    'CodeDocsSearchTool': MyCodeDocsSearchTool,
    'YahooFinanceNewsTool': MyYahooFinanceNewsTool,
    'TXTSearchTool': MyTXTSearchTool,
    'CSVSearchTool': MyCSVSearchTool,
    'DOCXSearchTool': MyDocxSearchTool,
    'EXASearchTool': MyEXASearchTool,
    'JSONSearchTool': MyJSONSearchTool,
    'MDXSearchTool': MyMDXSearchTool,
    'PDFSearchTool': MyPDFSearchTool,
    'PGSearchTool': MyPGSearchTool    
}
