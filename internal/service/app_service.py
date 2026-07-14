import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from injector import inject
from sqlalchemy import desc, func

from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.entity.app_entity import DEFAULT_APP_CONFIG, AppConfigType, AppStatus
from internal.entity.dataset_entity import RetrievalStrategy
from internal.exception import (
    FailException,
    NotFoundException,
    UnauthorizedException,
    ValidateException,
)
from internal.lib.helper import remove_fields
from internal.model import (
    Account,
    ApiTool,
    App,
    AppConfig,
    AppConfigVersion,
    AppDatasetJoin,
    Dataset,
)
from internal.schema.app_schema import (
    CreateAppReq,
    GetAppsWithPageReq,
    GetPublishHistoriesWithPageReq,
)
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy

from .app_config_service import AppConfigService
from .base_service import BaseService

# from internal.entity.audio_entity import ALLOWED_AUDIO_VOICES


@inject
@dataclass
class AppService(BaseService):
    """应用服务逻辑"""

    db: SQLAlchemy
    app_config_service: AppConfigService
    # language_model_manager: LanguageModelManager
    builtin_provider_manager: BuiltinProviderManager

    def get_apps_with_page(
        self, req: GetAppsWithPageReq, account: Account
    ) -> tuple[list[Any], Paginator]:
        """获取应用分页列表数据"""
        paginator = Paginator(db=self.db, req=req)
        filters = [App.account_id == account.id]
        if req.search_word.data:
            filters.append(App.name.ilike(f"%{req.search_word.data}%"))
        if req.status.data:
            filters.append(App.status == req.status.data)
        apps = paginator.paginate(
            self.db.session.query(App).filter(*filters).order_by(desc("created_at"))
        )
        return apps, paginator

    def create_app(self, req: CreateAppReq, account: Account) -> App:
        # 1. 开启数据库自动提交上下文
        with self.db.auto_commit():
            # 2.创建应用记录，并刷新数据，从而可以拿到应用id
            app = App(
                id=uuid.uuid4(),
                account_id=account.id,
                name=req.name.data,
                en_name=req.en_name.data,
                icon=req.icon.data,
                description=req.description.data,
                status=AppStatus.DRAFT,
            )
            self.db.session.add(app)
            self.db.session.flush()

            # 3.添加草稿记录
            app_config_version = AppConfigVersion(
                id=uuid.uuid4(),
                app_id=app.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                **DEFAULT_APP_CONFIG,
            )
            self.db.session.add(app_config_version)
            self.db.session.flush()

            # 4.为应用添加草稿配置id
            app.draft_app_config_id = app_config_version.id

        # 5.返回创建的应用记录
        return app

    def get_app(self, app_id: uuid.UUID, account: Account) -> App:
        """根据传递的id获取应用的基础信息"""
        # 1.查询数据库获取应用基础信息
        app = self.get(App, app_id)
        # 2.判断应用是否存在
        if not app:
            raise NotFoundException("应用不存在")
        # 3.判断当前账号是否有权限访问该应用
        if app.account_id != account.id:
            raise UnauthorizedException("当前账号无权限")
        return app

    def get_draft_app_config_in_get_app(self, app: App) -> AppConfigVersion:
        """获取指定应用的草稿配置，不存在时创建一份默认草稿配置。

        与只读属性 App.draft_app_config 不同，这里承担「取不到就创建」的业务行为，
        所有写入都收敛在一个受控事务里，并同步回写 app.draft_app_config_id，
        避免草稿配置存在两个不一致的真相源。
        """
        # 1.先通过只读属性尝试获取已有草稿配置
        draft_app_config = app.draft_app_config
        if draft_app_config is not None:
            return draft_app_config

        # 2.不存在则在单个事务里创建默认草稿配置并回写关联id
        with self.db.auto_commit():
            draft_app_config = AppConfigVersion(
                id=uuid.uuid4(),
                app_id=app.id,
                version=0,
                config_type=AppConfigType.DRAFT,
                **DEFAULT_APP_CONFIG,
            )
            self.db.session.add(draft_app_config)
            self.db.session.flush()
            app.draft_app_config_id = draft_app_config.id

        return draft_app_config

    def get_draft_app_config(
        self, app_id: uuid.UUID, account: Account
    ) -> dict[str, Any]:
        """根据传递的应用id，获取指定的应用草稿配置信息"""

        # 1.获取应用信息并校验权限
        app = self.get_app(app_id, account)
        return self.app_config_service.get_draft_app_config(app)

    def update_app(self, app_id: UUID, account: Account) -> App:
        """更新应用信息"""
        app = self.get_app(app_id, account)
        with self.db.auto_commit():
            app.name = "robin的机器人"
        return app

    def delete_app(self, app_id: UUID, account: Account) -> bool:
        """删除应用信息"""
        app = (
            self.db.session.query(App)
            .filter(App.id == app_id, App.account_id == account.id)
            .one_or_none()
        )
        if app is None:
            return False
        with self.db.auto_commit():
            self.db.session.delete(app)
        return True

    def _validate_draft_app_config(
        self, draft_app_config: dict[str, Any], account: Account
    ) -> dict[str, Any]:
        """校验传递的应用草稿配置信息，返回校验后的数据"""
        # 1.校验上传的草稿配置中对应的字段，至少拥有一个可以更新的配置
        acceptable_fields = [
            "model_config",
            "dialog_round",
            "preset_prompt",
            "tools",
            "workflows",
            "datasets",
            "retrieval_config",
            "long_term_memory",
            "opening_statement",
            "opening_questions",
            "speech_to_text",
            "text_to_speech",
            "suggested_after_answer",
            "review_config",
            "multimodal",
            "agents",
            "mcp_server",
        ]

        # 2.判断传递的草稿配置是否在可接受字段内
        if (
            not draft_app_config
            or not isinstance(draft_app_config, dict)
            or set(draft_app_config.keys()) - set(acceptable_fields)
        ):
            raise ValidateException("草稿配置字段出错，请核实后重试")

        # 3.校验model_config字段，provider/model使用严格校验(出错的时候直接抛出)，parameters使用宽松校验，出错时使用默认值
        # if "model_config" in draft_app_config:
        #     # 3.1 获取模型配置并判断数据是否为字典
        #     model_config = draft_app_config["model_config"]
        #     if not isinstance(model_config, dict):
        #         raise ValidateException("模型配置格式错误，请核实后重试")

        #     # 3.2 判断model_config键信息是否正确
        #     if set(model_config.keys()) != {
        #         "provider",
        #         "model",
        #         "parameters",
        #         "baseUrl",
        #         "apiKey",
        #     }:
        #         raise ValidateException("模型键配置格式错误，请核实后重试")

        #     # 3.3 判断模型提供者信息是否正确
        #     if not model_config["provider"] or not isinstance(
        #         model_config["provider"], str
        #     ):
        #         raise ValidateException("模型服务提供商类型必须为字符串")
        #     provider = self.language_model_manager.get_provider(
        #         model_config["provider"]
        #     )
        #     if not provider:
        #         raise ValidateException("该模型服务提供商不存在，请核实后重试")

        #     # 3.4 判断模型信息是否正确
        #     if not model_config["model"] or not isinstance(model_config["model"], str):
        #         raise ValidateException("模型名字必须是否字符串")
        #     model_entity = provider.get_model_entity(model_config["model"])
        #     if not model_entity:
        #         raise ValidateException("该服务提供商下不存在该模型，请核实后重试")

        #     # 3.5 判断传递的parameters是否正确，如果不正确则设置默认值，并剔除多余字段，补全未传递的字段
        #     parameters = {}
        #     for parameter in model_entity.parameters:
        #         # 3.6 从model_config中获取参数值，如果不存在则设置为默认值
        #         parameter_value = model_config["parameters"].get(
        #             parameter.name, parameter.default
        #         )

        #         # 3.7 判断参数是否必填
        #         if parameter.required:
        #             # 3.8 参数必填，则值不允许为None，如果为None则设置默认值
        #             if parameter_value is None:
        #                 parameter_value = parameter.default
        #             else:
        #                 # 3.9 值非空则校验数据类型是否正确，不正确则设置默认值
        #                 value_type = get_value_type(parameter_value)
        #                 if value_type != parameter.type.value:
        #                     if parameter.type.value == ModelParameterType.FLOAT.value:
        #                         parameter_value = float(parameter_value)
        #                     else:
        #                         parameter_value = parameter.default

        #         else:
        #             # 3.10 参数非必填，数据非空的情况下需要校验
        #             if parameter_value is not None:
        #                 value_type = get_value_type(parameter_value)
        #                 if value_type != parameter.type.value:
        #                     if parameter.type.value == ModelParameterType.FLOAT.value:
        #                         parameter_value = float(parameter_value)
        #                     else:
        #                         parameter_value = parameter.default

        #         # 3.11 判断参数是否存在options，如果存在则数值必须在options中选择
        #         if parameter.options and parameter_value not in parameter.options:
        #             parameter_value = parameter.default

        #         # 3.12 参数类型为int/float，如果存在min/max时候需要校验
        #         if (
        #             parameter.type in [ModelParameterType.INT, ModelParameterType.FLOAT]
        #             and parameter_value is not None
        #         ):
        #             # 3.13 校验数值的min/max
        #             if (parameter.min and parameter_value < parameter.min) or (
        #                 parameter.max and parameter_value > parameter.max
        #             ):
        #                 parameter_value = parameter.default

        #         parameters[parameter.name] = parameter_value

        #     # 3.13 覆盖Agent配置中的模型配置
        #     model_config["parameters"] = parameters
        #     draft_app_config["model_config"] = model_config

        # 4.校验dialog_round上下文轮数，校验数据类型以及范围
        if "dialog_round" in draft_app_config:
            dialog_round = draft_app_config["dialog_round"]
            if not isinstance(dialog_round, int) or not (0 <= dialog_round <= 100):
                raise ValidateException("携带上下文轮数范围为0-100")

        # 5.校验preset_prompt
        if "preset_prompt" in draft_app_config:
            preset_prompt = draft_app_config["preset_prompt"]
            if not isinstance(preset_prompt, str) or len(preset_prompt) > 2000:
                raise ValidateException(
                    "人设与回复逻辑必须是字符串，长度在0-2000个字符"
                )

        # 6.校验tools工具
        if "tools" in draft_app_config:
            tools = draft_app_config["tools"]
            validate_tools = []

            # 6.1 tools类型必须为列表，空列表则代表不绑定任何工具
            if not isinstance(tools, list):
                raise ValidateException("工具列表必须是列表型数据")
            # 6.2 tools的长度不能超过5
            if len(tools) > 5:
                raise ValidateException("Agent绑定的工具数不能超过5")
            # 6.3 循环校验工具里的每一个参数
            for tool in tools:
                # 6.4 校验tool非空并且类型为字典
                if not tool or not isinstance(tool, dict):
                    raise ValidateException("绑定插件工具参数出错")
                # 6.5 校验工具的参数是不是type、provider_id、tool_id、params
                if set(tool.keys()) != {"type", "provider_id", "tool_id", "params"}:
                    raise ValidateException("绑定插件工具参数出错")
                # 6.6 校验type类型是否为builtin_tool以及api_tool
                if tool["type"] not in ["builtin_tool", "api_tool"]:
                    raise ValidateException("绑定插件工具参数出错")
                # 6.7 校验provider_id和tool_id
                if (
                    not tool["provider_id"]
                    or not tool["tool_id"]
                    or not isinstance(tool["provider_id"], str)
                    or not isinstance(tool["tool_id"], str)
                ):
                    raise ValidateException("插件提供者或者插件标识参数出错")
                # 6.8 校验params参数，类型为字典
                if not isinstance(tool["params"], dict):
                    raise ValidateException("插件自定义参数格式错误")
                # 6.9 校验对应的工具是否存在，而且需要划分成builtin_tool和api_tool
                if tool["type"] == "builtin_tool":
                    builtin_tool = self.builtin_provider_manager.get_tool(
                        tool["provider_id"], tool["tool_id"]
                    )
                    if not builtin_tool:
                        continue
                else:
                    api_tool = (
                        self.db.session.query(ApiTool)
                        .filter(
                            ApiTool.provider_id == tool["provider_id"],
                            ApiTool.name == tool["tool_id"],
                            ApiTool.account_id == account.id,
                        )
                        .one_or_none()
                    )
                    if not api_tool:
                        continue

                validate_tools.append(tool)

            # 6.10 校验绑定的工具是否重复
            check_tools = [
                f"{tool['provider_id']}_{tool['tool_id']}" for tool in validate_tools
            ]
            if len(set(check_tools)) != len(validate_tools):
                raise ValidateException("绑定插件存在重复")

            # 6.11 重新赋值工具
            draft_app_config["tools"] = validate_tools

        # 校验workflow，提取已发布+权限正确的工作流列表进行绑定（更新配置阶段不校验）
        # if "workflows" in draft_app_config:
        #     workflows = draft_app_config["workflows"]

        #     if not isinstance(workflows, list):
        #         raise ValidateException("绑定工作流列表参数格式错误")
        #     if len(workflows) > 5:
        #         raise ValidateException("绑定工作流数量不能超过5个")
        #     for workflow_id in workflows:
        #         try:
        #             UUID(workflow_id)
        #         except Exception as _:
        #             raise ValidateException("工作流参数必须是UUID")
        #     if (len(set(workflows))) != len(workflows):
        #         raise ValidateException("绑定工作流存在重复")
        #     # workflow_records = (
        #     #     self.db.session.query(Workflow)
        #     #     .filter(
        #     #         Workflow.id.in_(workflows),
        #     #         Workflow.account_id == account.id,
        #     #         Workflow.status == WorkflowStatus.PUBLISHED,
        #     #     )
        #     #     .all()
        #     # )
        #     # workflow_sets = set(
        #     #     [str(workflow_record.id) for workflow_record in workflow_records]
        #     # )
        #     # draft_app_config["workflows"] = [
        #     #     workflow_id for workflow_id in workflows if workflow_id in workflow_sets
        #     # ]

        # 8.校验datasets知识库列表
        if "datasets" in draft_app_config:
            datasets = draft_app_config["datasets"]

            # 8.1 判断datasets类型是否为列表
            if not isinstance(datasets, list):
                raise ValidateException("绑定知识库列表参数格式错误")
            # 8.2 判断关联的知识库列表是否超过5个
            if len(datasets) > 5:
                raise ValidateException("Agent绑定的知识库数量不能超过5个")
            # 8.3 循环校验知识库的每个参数
            for dataset_id in datasets:
                try:
                    UUID(dataset_id)
                except Exception:
                    raise ValidateException("知识库列表参数必须是UUID") from None
            # 8.4 判断是否传递了重复的知识库
            if len(set(datasets)) != len(datasets):
                raise ValidateException("绑定知识库存在重复")
            # 8.5 校验绑定的知识库权限，剔除不属于当前账号的知识库
            dataset_records = (
                self.db.session.query(Dataset)
                .filter(
                    Dataset.id.in_(datasets),
                    Dataset.account_id == account.id,
                )
                .all()
            )
            dataset_sets = {
                str(dataset_record.id) for dataset_record in dataset_records
            }
            draft_app_config["datasets"] = [
                dataset_id for dataset_id in datasets if dataset_id in dataset_sets
            ]

        # 9.校验retrieval_config检索配置
        if "retrieval_config" in draft_app_config:
            retrieval_config = draft_app_config["retrieval_config"]

            # 9.1 判断检索配置非空且类型为字典
            if not retrieval_config or not isinstance(retrieval_config, dict):
                raise ValidateException("检索配置格式错误")
            # 9.2 校验检索配置的字段类型
            if set(retrieval_config.keys()) != {"retrieval_strategy", "k", "score"}:
                raise ValidateException("检索配置格式错误")
            # 9.3 校验检索策略是否正确
            if retrieval_config["retrieval_strategy"] not in [
                rc.value for rc in RetrievalStrategy
            ]:
                raise ValidateException("检测策略格式错误")
            # 9.4 校验最大召回数量
            if not isinstance(retrieval_config["k"], int) or not (
                0 <= retrieval_config["k"] <= 10
            ):
                raise ValidateException("最大召回数量范围为0-10")
            # 9.5 校验得分/最小匹配度
            if not isinstance(retrieval_config["score"], float) or not (
                0 <= retrieval_config["score"] <= 1
            ):
                raise ValidateException("最小匹配范围为0-1")

        # 10.校验long_term_memory长期记忆配置
        if "long_term_memory" in draft_app_config:
            long_term_memory = draft_app_config["long_term_memory"]

            # 10.1 校验长期记忆格式
            if not long_term_memory or not isinstance(long_term_memory, dict):
                raise ValidateException("长期记忆设置格式错误")
            # 10.2 校验长期记忆属性
            if set(long_term_memory.keys()) != {"enable"} or not isinstance(
                long_term_memory["enable"], bool
            ):
                raise ValidateException("长期记忆设置格式错误")

        # 11.校验opening_statement对话开场白
        if "opening_statement" in draft_app_config:
            opening_statement = draft_app_config["opening_statement"]

            # 11.1 校验对话开场白类型以及长度
            if not isinstance(opening_statement, str) or len(opening_statement) > 2000:
                raise ValidateException("对话开场白的长度范围是0-2000")

        # 12.校验opening_questions开场建议问题列表
        if "opening_questions" in draft_app_config:
            opening_questions = draft_app_config["opening_questions"]

            # 12.1 校验是否为列表，并且长度不超过3
            if not isinstance(opening_questions, list) or len(opening_questions) > 3:
                raise ValidateException("开场建议问题不能超过3个")
            # 12.2 开场建议问题每个元素都是一个字符串
            for opening_question in opening_questions:
                if not isinstance(opening_question, str):
                    raise ValidateException("开场建议问题必须是字符串")

        # 13.校验speech_to_text语音转文本
        if "speech_to_text" in draft_app_config:
            speech_to_text = draft_app_config["speech_to_text"]

            # 13.1 校验语音转文本格式
            if not speech_to_text or not isinstance(speech_to_text, dict):
                raise ValidateException("语音转文本设置格式错误")
            # 13.2 校验语音转文本属性
            if set(speech_to_text.keys()) != {"enable"} or not isinstance(
                speech_to_text["enable"], bool
            ):
                raise ValidateException("语音转文本设置格式错误")

        # 14.校验text_to_speech文本转语音设置
        if "text_to_speech" in draft_app_config:
            text_to_speech = draft_app_config["text_to_speech"]

            # 14.1 校验字典格式
            if not isinstance(text_to_speech, dict):
                raise ValidateException("文本转语音设置格式错误")
            # 14.2 校验字段类型
            if (
                set(text_to_speech.keys()) != {"enable", "voice", "auto_play"}
                or not isinstance(text_to_speech["enable"], bool)
                # or text_to_speech["voice"] not in ALLOWED_AUDIO_VOICES
                or not isinstance(text_to_speech["auto_play"], bool)
            ):
                raise ValidateException("文本转语音设置格式错误")

        # 15.校验回答后生成建议问题
        if "suggested_after_answer" in draft_app_config:
            suggested_after_answer = draft_app_config["suggested_after_answer"]

            # 15.1 校验回答后建议问题格式
            if not suggested_after_answer or not isinstance(
                suggested_after_answer, dict
            ):
                raise ValidateException("回答后建议问题设置格式错误")
            # 15.2 校验回答后建议问题格式
            if set(suggested_after_answer.keys()) != {"enable"} or not isinstance(
                suggested_after_answer["enable"], bool
            ):
                raise ValidateException("回答后建议问题设置格式错误")

        # 16.校验review_config审核配置
        if "review_config" in draft_app_config:
            review_config = draft_app_config["review_config"]

            # 16.1 校验字段格式，非空
            if not review_config or not isinstance(review_config, dict):
                raise ValidateException("审核配置格式错误")
            # 16.2 校验字段信息
            if set(review_config.keys()) != {
                "enable",
                "keywords",
                "inputs_config",
                "outputs_config",
            }:
                raise ValidateException("审核配置格式错误")
            # 16.3 校验enable
            if not isinstance(review_config["enable"], bool):
                raise ValidateException("review.enable格式错误")
            # 16.4 校验keywords
            if (
                not isinstance(review_config["keywords"], list)
                or (review_config["enable"] and len(review_config["keywords"]) == 0)
                or len(review_config["keywords"]) > 100
            ):
                raise ValidateException("review.keywords非空且不能超过100个关键词")
            for keyword in review_config["keywords"]:
                if not isinstance(keyword, str):
                    raise ValidateException("review.keywords敏感词必须是字符串")
            # 16.5 校验inputs_config输入配置
            if (
                not review_config["inputs_config"]
                or not isinstance(review_config["inputs_config"], dict)
                or set(review_config["inputs_config"].keys())
                != {"enable", "preset_response"}
                or not isinstance(review_config["inputs_config"]["enable"], bool)
                or not isinstance(
                    review_config["inputs_config"]["preset_response"], str
                )
            ):
                raise ValidateException("review.inputs_config必须是一个字典")
            # 16.6 校验outputs_config输出配置
            if (
                not review_config["outputs_config"]
                or not isinstance(review_config["outputs_config"], dict)
                or set(review_config["outputs_config"].keys()) != {"enable"}
                or not isinstance(review_config["outputs_config"]["enable"], bool)
            ):
                raise ValidateException("review.outputs_config格式错误")
            # 16.7 在开启审核模块的时候，必须确保inputs_config或者是outputs_config至少有一个是开启的
            if review_config["enable"]:
                if (
                    review_config["inputs_config"]["enable"] is False
                    and review_config["outputs_config"]["enable"] is False
                ):
                    raise ValidateException("输入审核和输出审核至少需要开启一项")

                if (
                    review_config["inputs_config"]["enable"]
                    and review_config["inputs_config"]["preset_response"].strip() == ""
                ):
                    raise ValidateException("输入审核预设响应不能为空")

        return draft_app_config

    def update_draft_app_config(
        self, app_id: UUID, draft_app_config: dict[str, Any], account: Account
    ) -> AppConfigVersion:
        """根据传递的应用id+草稿配置修改指定应用的最新草稿"""

        # 1.获取应用信息并校验
        app = self.get_app(app_id, account)

        # 2.校验传递的草稿配置信息
        draft_app_config = self._validate_draft_app_config(draft_app_config, account)

        # 3.获取当前应用的最新草稿信息（不存在时创建默认草稿，确保有目标记录可更新）
        draft_app_config_record = self.get_draft_app_config_in_get_app(app)
        self.update(
            draft_app_config_record,
            updated_at=datetime.now(),
            **draft_app_config,
        )
        if app.status == AppStatus.PUBLISHED:
            self.update(app, status=AppStatus.REPUBLISH)
        return draft_app_config_record

    def publish_draft_app_config(self, app_id: UUID, account: Account) -> App:
        """根据传递的应用id+账号，发布/更新指定的应用草稿配置为运行时配置"""
        # 1.获取应用的信息以及草稿信息
        app = self.get_app(app_id, account)
        draft_app_config = self.get_draft_app_config(app_id, account)
        # get_draft_app_config 返回的是给前端使用的展示数据。为避免泄露模型
        # API Key，其中不会包含 model_config；发布时需从已校验并回写的草稿记录
        # 中读取。同时 workflows 当前也未包含在展示数据中，兼容从草稿记录读取。
        draft_app_config_record = app.draft_app_config
        model_config = (
            draft_app_config_record.model_config
            if draft_app_config_record and draft_app_config_record.model_config
            else DEFAULT_APP_CONFIG["model_config"]
        )
        workflows = (
            draft_app_config_record.workflows
            if draft_app_config_record and draft_app_config_record.workflows
            else []
        )

        # 2.创建应用运行配置（在这里暂时不删除历史的运行配置）
        app_config = self.create(
            AppConfig,
            app_id=app_id,
            model_config=model_config,
            dialog_round=draft_app_config["dialog_round"],
            preset_prompt=draft_app_config["preset_prompt"],
            tools=[
                {
                    "type": tool["type"],
                    "provider_id": tool["provider"]["id"],
                    "tool_id": tool["tool"]["name"],
                    "params": tool["tool"]["params"],
                }
                for tool in draft_app_config["tools"]
            ],
            # workflows=[workflow["id"] for workflow in draft_app_config["workflows"]],
            workflows=workflows,
            retrieval_config=draft_app_config["retrieval_config"],
            long_term_memory=draft_app_config["long_term_memory"],
            opening_statement=draft_app_config["opening_statement"],
            opening_questions=draft_app_config["opening_questions"],
            speech_to_text=draft_app_config["speech_to_text"],
            text_to_speech=draft_app_config["text_to_speech"],
            suggested_after_answer=draft_app_config["suggested_after_answer"],
            review_config=draft_app_config["review_config"],
            multimodal=draft_app_config["multimodal"],
            agents=[app["id"] for app in draft_app_config["agents"]],
        )

        # 3.更新应用关联的运行时配置以及状态
        self.update(app, app_config_id=app_config.id, status=AppStatus.PUBLISHED)

        # 4.先删除原有的知识库关联记录
        with self.db.auto_commit():
            self.db.session.query(AppDatasetJoin).filter(
                AppDatasetJoin.app_id == app_id,
            ).delete()

        # 5.新增新的知识库关联记录
        for dataset in draft_app_config["datasets"]:
            self.create(AppDatasetJoin, app_id=app_id, dataset_id=dataset["id"])

        # 获取应用草稿记录，并移除id、version、config_type、updated_at、created_at字段
        draft_app_config_copy = app.draft_app_config.__dict__.copy()
        remove_fields(
            draft_app_config_copy,
            [
                "id",
                "version",
                "config_type",
                "updated_at",
                "created_at",
                "_sa_instance_state",
            ],
        )

        # 获取当前最大的发布版本
        max_version = (
            self.db.session.query(func.coalesce(func.max(AppConfigVersion.version), 0))
            .filter(
                AppConfigVersion.app_id == app_id,
                AppConfigVersion.config_type == AppConfigType.PUBLISHED,
            )
            .scalar()
        )

        # 新增发布历史配置
        self.create(
            AppConfigVersion,
            version=max_version + 1,
            config_type=AppConfigType.PUBLISHED,
            **draft_app_config_copy,
        )

        return app

    def cancel_publish_app_config(self, app_id: UUID, account: Account) -> App:
        """根据传递的应用id+账号，取消发布指定的应用配置"""
        # 获取应用信息并校验权限
        app = self.get_app(app_id, account)

        # 检测下当前应用的状态是否为已发布
        if app.status == AppStatus.DRAFT:
            raise FailException("当前应用未发布，请核实后重试")

        # 修改账号的发布状态，并清空关联配置id
        self.update(app, status=AppStatus.DRAFT, app_config_id=None)

        # 删除应用关联的知识库信息
        with self.db.auto_commit():
            self.db.session.query(AppDatasetJoin).filter(
                AppDatasetJoin.app_id == app_id,
            ).delete()

        return app

    def get_publish_histories_with_page(
        self, app_id: UUID, req: GetPublishHistoriesWithPageReq, account: Account
    ) -> tuple[list[AppConfigVersion], Paginator]:
        """根据传递的应用id+请求数据，获取指定应用的发布历史配置列表信息"""
        # 获取应用信息并校验权限
        self.get_app(app_id, account)

        # 构建分页器
        paginator = Paginator(db=self.db, req=req)

        # 执行分页并获取数据
        app_config_versions = paginator.paginate(
            self.db.session.query(AppConfigVersion)
            .filter(
                AppConfigVersion.app_id == app_id,
                AppConfigVersion.config_type == AppConfigType.PUBLISHED,
            )
            # 按照版本进行倒序排列输出
            .order_by(desc("version"))
        )

        return app_config_versions, paginator
