from agentops import record_tool
import streamlit as st
import os
from utils import rnd_id
from crewai_tools import (
    CodeInterpreterTool, ScrapeElementFromWebsiteTool, TXTSearchTool, SeleniumScrapingTool,
    PGSearchTool, PDFSearchTool, MDXSearchTool, JSONSearchTool, GithubSearchTool,
    EXASearchTool, DOCXSearchTool, CSVSearchTool, ScrapeWebsiteTool, FileReadTool,
    DirectorySearchTool, DirectoryReadTool, CodeDocsSearchTool, YoutubeVideoSearchTool,
    SerperDevTool, YoutubeChannelSearchTool, WebsiteSearchTool
)
from custom_tools import CustomApiTool, CustomFileWriteTool, CustomCodeInterpreterTool
from langchain_community.tools import YahooFinanceNewsTool
class MyTool:
    def __init__(self, tool_id, name, description, parameters, **kwargs):
        self.tool_id = tool_id or rnd_id()
        self.name = name
        self.description = description
        self.parameters = kwargs
        self.parameters_metadata = parameters

    def create_tool(self):
        pass

    def get_parameters(self):
        return self.parameters

    def set_parameters(self, **kwargs):
        self.parameters.update(kwargs)

    def get_parameter_names(self):
        return list(self.parameters_metadata.keys())

    def is_parameter_mandatory(self, param_name):
        return self.parameters_metadata.get(param_name, {}).get('mandatory', False)

    def is_valid(self, show_warning=False):
        for param_name, metadata in self.parameters_metadata.items():
            if metadata['mandatory'] and not self.parameters.get(param_name):
                if show_warning:
                    st.warning(f"Parameter '{param_name}' is mandatory for tool '{self.name}'")
                return False
        return True

class MyScrapeWebsiteTool(MyTool):
    def __init__(self, tool_id=None, website_url=None):
        parameters = {
            'website_url': {'mandatory': False}
        }
        super().__init__(tool_id, 'ScrapeWebsiteTool', "A tool that can be used to read website content.", parameters, website_url=website_url)

    @record_tool('ScrapeWebsiteTool')
    def create_tool(self) -> ScrapeWebsiteTool:
        return ScrapeWebsiteTool(self.parameters.get('website_url') if self.parameters.get('website_url') else None)

class MyFileReadTool(MyTool):
    def __init__(self, tool_id=None, file_path=None):
        parameters = {
            'file_path': {'mandatory': False}
        }
        super().__init__(tool_id, 'FileReadTool', "A tool that can be used to read a file's content.", parameters, file_path=file_path)

    @record_tool('FileReadTool')
    def create_tool(self) -> FileReadTool:
        return FileReadTool(self.parameters.get('file_path') if self.parameters.get('file_path') else None)

class MyDirectorySearchTool(MyTool):
    def __init__(self, tool_id=None, directory=None):
        parameters = {
            'directory': {'mandatory': True}
        }
        super().__init__(tool_id, 'DirectorySearchTool',
            "A tool that can be used to semantic search a query from a directory's content within the workspace.",
            parameters, directory=directory)
        
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
            safe_path = self._create_directory(directory)
            placeholder_path = os.path.join(safe_path, '.indexme')
            if not os.path.exists(placeholder_path):
                with open(placeholder_path, 'w') as f:
                    f.write('Directory created for semantic search')
            
            tool = DirectorySearchTool()
            tool.directory = safe_path
            return tool
            
        except Exception as e:
            raise ValueError(f"Failed to initialize directory tool: {str(e)}")

    def is_valid(self, show_warning=False):
        directory = self.parameters.get('directory')
        
        if not directory:
            if show_warning:
                st.warning("Directory parameter is required")
            return False
            
        try:
            safe_path = self._create_directory(directory)
            return True
            
        except ValueError as e:
            if show_warning:
                st.warning(str(e))
            return False
        except Exception as e:
            if show_warning:
                st.warning(f"Error creating/validating directory: {str(e)}")
            return False

class MyDirectoryReadTool(MyTool):
    def __init__(self, tool_id=None, directory_contents=None):
        parameters = {
            'directory_contents': {'mandatory': True}
        }
        super().__init__(tool_id, 'DirectoryReadTool', "Use the tool to list the contents of the specified directory", parameters, directory_contents=directory_contents)

    @record_tool('DirectoryReadTool')
    def create_tool(self) -> DirectoryReadTool:
        return DirectoryReadTool(self.parameters.get('directory_contents'))

class MyCodeDocsSearchTool(MyTool):
    def __init__(self, tool_id=None, code_docs=None):
        parameters = {
            'code_docs': {'mandatory': False}
        }
        super().__init__(tool_id, 'CodeDocsSearchTool', "A tool that can be used to search through code documentation.", parameters, code_docs=code_docs)

    @record_tool('CodeDocsSearchTool')
    def create_tool(self) -> CodeDocsSearchTool:
        return CodeDocsSearchTool(self.parameters.get('code_docs') if self.parameters.get('code_docs') else None)

class MyYoutubeVideoSearchTool(MyTool):
    def __init__(self, tool_id=None, youtube_video_url=None):
        parameters = {
            'youtube_video_url': {'mandatory': False}
        }
        super().__init__(tool_id, 'YoutubeVideoSearchTool', "A tool that can be used to semantic search a query from a Youtube Video content.", parameters, youtube_video_url=youtube_video_url)

    @record_tool('YoutubeVideoSearchTool')
    def create_tool(self) -> YoutubeVideoSearchTool:
        return YoutubeVideoSearchTool(self.parameters.get('youtube_video_url') if self.parameters.get('youtube_video_url') else None)

class MySerperDevTool(MyTool):
    def __init__(self, tool_id=None, SERPER_API_KEY=None):
        parameters = {
            'SERPER_API_KEY': {'mandatory': True}
        }
        super().__init__(tool_id, 'SerperDevTool', "A tool that can be used to search the internet with a search_query", parameters)

    @record_tool('SerperDevTool')
    def create_tool(self) -> SerperDevTool:
        os.environ['SERPER_API_KEY'] = self.parameters.get('SERPER_API_KEY')
        return SerperDevTool()
    
class MyYoutubeChannelSearchTool(MyTool):
    def __init__(self, tool_id=None, youtube_channel_handle=None):
        parameters = {
            'youtube_channel_handle': {'mandatory': False}
        }
        super().__init__(tool_id, 'YoutubeChannelSearchTool', "A tool that can be used to semantic search a query from a Youtube Channels content. Channel can be added as @channel", parameters, youtube_channel_handle=youtube_channel_handle)

    @record_tool('YoutubeChannelSearchTool')
    def create_tool(self) -> YoutubeChannelSearchTool:
        return YoutubeChannelSearchTool(self.parameters.get('youtube_channel_handle') if self.parameters.get('youtube_channel_handle') else None)

class MyWebsiteSearchTool(MyTool):
    def __init__(self, tool_id=None, website=None):
        parameters = {
            'website': {'mandatory': False}
        }
        super().__init__(tool_id, 'WebsiteSearchTool', "A tool that can be used to semantic search a query from a specific URL content.", parameters, website=website)

    @record_tool('WebsiteSearchTool')
    def create_tool(self) -> WebsiteSearchTool:
        return WebsiteSearchTool(self.parameters.get('website') if self.parameters.get('website') else None)
   
class MyCSVSearchTool(MyTool):
    def __init__(self, tool_id=None, csv=None):
        parameters = {
            'csv': {'mandatory': False}
        }
        super().__init__(tool_id, 'CSVSearchTool', "A tool that can be used to semantic search a query from a CSV's content.", parameters, csv=csv)

    @record_tool('CSVSearchTool')
    def create_tool(self) -> CSVSearchTool:
        return CSVSearchTool(csv=self.parameters.get('csv') if self.parameters.get('csv') else None)

class MyDocxSearchTool(MyTool):
    def __init__(self, tool_id=None, docx=None):
        parameters = {
            'docx': {'mandatory': False}
        }
        super().__init__(tool_id, 'DOCXSearchTool', "A tool that can be used to semantic search a query from a DOCX's content.", parameters, docx=docx)

    @record_tool('DOCXSearchTool')
    def create_tool(self) -> DOCXSearchTool:
        return DOCXSearchTool(docx=self.parameters.get('docx') if self.parameters.get('docx') else None)

class MyEXASearchTool(MyTool):
    def __init__(self, tool_id=None, EXA_API_KEY=None):
        parameters = {
            'EXA_API_KEY': {'mandatory': True}
        }
        super().__init__(tool_id, 'EXASearchTool', "A tool that can be used to search the internet from a search_query", parameters, EXA_API_KEY=EXA_API_KEY)

    @record_tool('EXASearchTool')
    def create_tool(self) -> EXASearchTool:
        os.environ['EXA_API_KEY'] = self.parameters.get('EXA_API_KEY')
        return EXASearchTool()

class MyGithubSearchTool(MyTool):
    def __init__(self, tool_id=None, github_repo=None, gh_token=None, content_types=None):
        parameters = {
            'github_repo': {'mandatory': False},
            'gh_token': {'mandatory': True},
            'content_types': {'mandatory': False}
        }
        super().__init__(tool_id, 'GithubSearchTool', "A tool that can be used to semantic search a query from a Github repository's content. Valid content_types: code,repo,pr,issue (comma separated)", parameters, github_repo=github_repo, gh_token=gh_token, content_types=content_types)

    @record_tool('GithubSearchTool')
    def create_tool(self) -> GithubSearchTool:
        return GithubSearchTool(
            github_repo=self.parameters.get('github_repo') if self.parameters.get('github_repo') else None,
            gh_token=self.parameters.get('gh_token'),
            content_types=self.parameters.get('search_query').split(",") if self.parameters.get('search_query') else ["code", "repo", "pr", "issue"]
        )

class MyJSONSearchTool(MyTool):
    def __init__(self, tool_id=None, json_path=None):
        parameters = {
            'json_path': {'mandatory': False}
        }
        super().__init__(tool_id, 'JSONSearchTool', "A tool that can be used to semantic search a query from a JSON's content.", parameters, json_path=json_path)

    @record_tool('JSONSearchTool')
    def create_tool(self) -> JSONSearchTool:
        return JSONSearchTool(json_path=self.parameters.get('json_path') if self.parameters.get('json_path') else None)

class MyMDXSearchTool(MyTool):
    def __init__(self, tool_id=None, mdx=None):
        parameters = {
            'mdx': {'mandatory': False}
        }
        super().__init__(tool_id, 'MDXSearchTool', "A tool that can be used to semantic search a query from a MDX's content.", parameters, mdx=mdx)

    @record_tool('MDXSearchTool')
    def create_tool(self) -> MDXSearchTool:
        return MDXSearchTool(mdx=self.parameters.get('mdx') if self.parameters.get('mdx') else None)
    
class MyPDFSearchTool(MyTool):
    def __init__(self, tool_id=None, pdf=None):
        parameters = {
            'pdf': {'mandatory': False}
        }
        super().__init__(tool_id, 'PDFSearchTool', "A tool that can be used to semantic search a query from a PDF's content.", parameters, pdf=pdf)

    @record_tool('PDFSearchTool')
    def create_tool(self) -> PDFSearchTool:
        return PDFSearchTool(self.parameters.get('pdf') if self.parameters.get('pdf') else None)

class MyPGSearchTool(MyTool):
    def __init__(self, tool_id=None, db_uri=None):
        parameters = {
            'db_uri': {'mandatory': True}
        }
        super().__init__(tool_id, 'PGSearchTool', "A tool that can be used to semantic search a query from a database table's content.", parameters, db_uri=db_uri)

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
        super().__init__(
            tool_id, 
            'SeleniumScrapingTool', 
            "A tool that can be used to read a specific part of website content. CSS elements are separated by comma, cookies are in format {key1:value1},{key2:value2}", 
            parameters, 
            website_url=website_url, 
            css_element=css_element, 
            cookie=cookie, 
            wait_time=wait_time
)
    @record_tool('SeleniumScrapingTool')
    def create_tool(self) -> SeleniumScrapingTool:
        cookie_arrayofdicts = [{k: v} for k, v in (item.strip('{}').split(':') for item in self.parameters.get('cookie', '').split(','))] if self.parameters.get('cookie') else None

        return SeleniumScrapingTool(
            website_url=self.parameters.get('website_url') if self.parameters.get('website_url') else None,
            css_element=self.parameters.get('css_element').split(',') if self.parameters.get('css_element') else None,
            cookie=cookie_arrayofdicts,
            wait_time=self.parameters.get('wait_time') if self.parameters.get('wait_time') else 10
        )

class MyTXTSearchTool(MyTool):
    def __init__(self, tool_id=None, txt=None):
        parameters = {
            'txt': {'mandatory': False}
        }
        super().__init__(tool_id, 'TXTSearchTool', "A tool that can be used to semantic search a query from a TXT's content.", parameters, txt=txt)

    @record_tool('TXTSearchTool')
    def create_tool(self) -> TXTSearchTool:
        return TXTSearchTool(self.parameters.get('txt'))

class MyScrapeElementFromWebsiteTool(MyTool):
    def __init__(self, tool_id=None, website_url=None, css_element=None, cookie=None):
        parameters = {
            'website_url': {'mandatory': False},
            'css_element': {'mandatory': False},
            'cookie': {'mandatory': False}
        }
        super().__init__(
            tool_id, 
            'ScrapeElementFromWebsiteTool', 
            "A tool that can be used to read a specific part of website content. CSS elements are separated by comma, cookies are in format {key1:value1},{key2:value2}", 
            parameters, 
            website_url=website_url, 
            css_element=css_element, 
            cookie=cookie
        )

    @record_tool('ScrapeElementFromWebsiteTool')
    def create_tool(self) -> ScrapeElementFromWebsiteTool:
        cookie_arrayofdicts = [{k: v} for k, v in (item.strip('{}').split(':') for item in self.parameters.get('cookie', '').split(','))] if self.parameters.get('cookie') else None
        return ScrapeElementFromWebsiteTool(
            website_url=self.parameters.get('website_url') if self.parameters.get('website_url') else None,
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
    
class MyCustomApiTool(MyTool):
    def __init__(self, tool_id=None, base_url=None, headers=None, query_params=None):
        parameters = {
            'base_url': {'mandatory': False},
            'headers': {'mandatory': False},
            'query_params': {'mandatory': False}
        }
        super().__init__(tool_id, 'CustomApiTool', "A tool that can be used to make API calls with customizable parameters.", parameters, base_url=base_url, headers=headers, query_params=query_params)

    @record_tool('CustomApiTool')
    def create_tool(self) -> CustomApiTool:
        return CustomApiTool(
            base_url=self.parameters.get('base_url') if self.parameters.get('base_url') else None,
            headers=eval(self.parameters.get('headers')) if self.parameters.get('headers') else None,
            query_params=self.parameters.get('query_params') if self.parameters.get('query_params') else None
        )

class MyCustomFileWriteTool(MyTool):
    def __init__(self, tool_id=None, base_folder=None, filename=None):
        parameters = {
            'base_folder': {'mandatory': True},
            'filename': {'mandatory': False}
        }
        super().__init__(tool_id, 'CustomFileWriteTool', "A tool that can be used to write a file to a specific folder.", parameters,base_folder=base_folder, filename=filename)

    @record_tool('CustomFileWriteTool')
    def create_tool(self) -> CustomFileWriteTool:
        return CustomFileWriteTool(
            base_folder=self.parameters.get('base_folder') if self.parameters.get('base_folder') else "workspace",
            filename=self.parameters.get('filename') if self.parameters.get('filename') else None
        )


class MyCodeInterpreterTool(MyTool):
    def __init__(self, tool_id=None):
        parameters = {}
        super().__init__(tool_id, 'CodeInterpreterTool', "This tool is used to give the Agent the ability to run code (Python3) from the code generated by the Agent itself. The code is executed in a sandboxed environment, so it is safe to run any code. Docker required.", parameters)

    @record_tool('CodeInterpreterTool')
    def create_tool(self) -> CodeInterpreterTool:
        return CodeInterpreterTool()
    

class MyCustomCodeInterpreterTool(MyTool):
    def __init__(self, tool_id=None,workspace_dir=None):
        parameters = {
            'workspace_dir': {'mandatory': False}
        }
        super().__init__(tool_id, 'CustomCodeInterpreterTool', "This tool is used to give the Agent the ability to run code (Python3) from the code generated by the Agent itself. The code is executed in a sandboxed environment, so it is safe to run any code. Workspace folder is shared. Docker required.", parameters, workspace_dir=workspace_dir)

    @record_tool('CustomCodeInterpreterTool')
    def create_tool(self) -> CustomCodeInterpreterTool:
        return CustomCodeInterpreterTool(workspace_dir=self.parameters.get('workspace_dir') if self.parameters.get('workspace_dir') else "workspace")

TOOL_CLASSES = {
    'SerperDevTool': MySerperDevTool,
    'WebsiteSearchTool': MyWebsiteSearchTool,
    'ScrapeWebsiteTool': MyScrapeWebsiteTool,
    'SeleniumScrapingTool': MySeleniumScrapingTool,
    'ScrapeElementFromWebsiteTool': MyScrapeElementFromWebsiteTool,
    'CustomApiTool': MyCustomApiTool,
    'CodeInterpreterTool': MyCodeInterpreterTool,
    'CustomCodeInterpreterTool': MyCustomCodeInterpreterTool,
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