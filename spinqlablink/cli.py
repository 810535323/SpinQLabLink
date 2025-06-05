# Copyright 2025 SpinQ Technology Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
SpinQLabLink命令行接口
"""

import argparse
import sys
import json
import uuid
from typing import Dict, Any

from .spinqlablink import api
from .utils import LoggerManager, setup_default_logger


def setup_parser() -> argparse.ArgumentParser:
    """设置命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="SpinQLabLink - SpinQ量子实验远程客户端",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # 设置日志级别
    parser.add_argument('--log-level', choices=['debug', 'info', 'warning', 'error'],
                      default='info', help='日志级别 (默认: info)')
    
    # 设置日志目录
    parser.add_argument('--log-dir', default=None, help='日志目录路径')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 启动实验命令
    start_parser = subparsers.add_parser('start', help='启动新实验')
    start_parser.add_argument('--type', required=True, help='实验类型 (circuit, pulse, calibration)')
    start_parser.add_argument('--config', required=True, help='实验配置文件路径 (JSON格式)')
    start_parser.add_argument('--id', default=None, help='实验ID (默认自动生成)')
    
    # 上传数据命令
    upload_parser = subparsers.add_parser('upload', help='上传实验数据')
    upload_parser.add_argument('--id', required=True, help='实验ID')
    upload_parser.add_argument('--data', required=True, help='数据文件路径 (JSON格式)')
    
    # 结束实验命令
    finish_parser = subparsers.add_parser('finish', help='结束实验')
    finish_parser.add_argument('--id', required=True, help='实验ID')
    finish_parser.add_argument('--status', choices=['completed', 'failed', 'canceled'],
                             default='completed', help='实验结束状态')
    finish_parser.add_argument('--message', default=None, help='附加信息')
    
    # 获取结果命令
    result_parser = subparsers.add_parser('result', help='获取实验结果')
    result_parser.add_argument('--id', required=True, help='实验ID')
    result_parser.add_argument('--format', choices=['json', 'csv'], default='json',
                             help='结果格式 (默认: json)')
    result_parser.add_argument('--output', default=None, help='输出文件路径')
    
    # 获取状态命令
    status_parser = subparsers.add_parser('status', help='获取实验状态')
    status_parser.add_argument('--id', required=True, help='实验ID')
    
    # 获取实验列表命令
    list_parser = subparsers.add_parser('list', help='获取实验列表')
    list_parser.add_argument('--limit', type=int, default=10, help='返回数量限制 (默认: 10)')
    list_parser.add_argument('--offset', type=int, default=0, help='返回偏移量 (默认: 0)')
    list_parser.add_argument('--filter', default=None, help='过滤条件 (JSON格式)')
    
    return parser


def load_json_file(file_path: str) -> Dict[str, Any]:
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"错误: 无法加载JSON文件 '{file_path}': {e}")
        sys.exit(1)


def save_json_file(file_path: str, data: Dict[str, Any]) -> None:
    """保存JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {file_path}")
    except Exception as e:
        print(f"错误: 无法保存JSON文件 '{file_path}': {e}")
        sys.exit(1)


def handle_start_experiment(args):
    """处理启动实验命令"""
    # 加载配置文件
    config = load_json_file(args.config)
    
    # 生成实验ID
    experiment_id = args.id or str(uuid.uuid4())
    
    # 启动实验
    success = api.start_experiment(
        experiment_id=experiment_id,
        experiment_type=args.type,
        config=config
    )
    
    if success:
        print(f"实验启动成功，ID: {experiment_id}")
    else:
        print(f"实验启动失败")
        sys.exit(1)


def handle_upload_data(args):
    """处理上传数据命令"""
    # 加载数据文件
    data = load_json_file(args.data)
    
    # 上传数据
    success = api.upload_experiment_data(
        experiment_id=args.id,
        data=data
    )
    
    if success:
        print(f"数据上传成功，实验ID: {args.id}")
    else:
        print(f"数据上传失败")
        sys.exit(1)


def handle_finish_experiment(args):
    """处理结束实验命令"""
    # 结束实验
    success = api.finish_experiment(
        experiment_id=args.id,
        status=args.status,
        message=args.message
    )
    
    if success:
        print(f"实验结束成功，ID: {args.id}，状态: {args.status}")
    else:
        print(f"实验结束失败")
        sys.exit(1)


def handle_get_result(args):
    """处理获取结果命令"""
    # 获取结果
    result = api.get_experiment_result(
        experiment_id=args.id,
        result_format=args.format
    )
    
    if not result.get('success'):
        print(f"获取结果失败: {result.get('error', '未知错误')}")
        sys.exit(1)
    
    # 输出结果
    if args.output:
        save_json_file(args.output, result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def handle_get_status(args):
    """处理获取状态命令"""
    # 获取状态
    status = api.get_experiment_status(experiment_id=args.id)
    
    if not status.get('success'):
        print(f"获取状态失败: {status.get('error', '未知错误')}")
        sys.exit(1)
    
    print(json.dumps(status, ensure_ascii=False, indent=2))


def handle_list_experiments(args):
    """处理获取实验列表命令"""
    # 解析过滤条件
    filters = None
    if args.filter:
        try:
            filters = json.loads(args.filter)
        except json.JSONDecodeError:
            print(f"错误: 无效的过滤条件JSON")
            sys.exit(1)
    
    # 获取实验列表
    experiments = api.list_experiments(
        filters=filters,
        limit=args.limit,
        offset=args.offset
    )
    
    print(json.dumps(experiments, ensure_ascii=False, indent=2))


def main():
    """主函数"""
    parser = setup_parser()
    args = parser.parse_args()
    
    # 设置日志器
    setup_default_logger(log_level=args.log_level, log_dir=args.log_dir)
    
    # 处理命令
    if args.command == 'start':
        handle_start_experiment(args)
    elif args.command == 'upload':
        handle_upload_data(args)
    elif args.command == 'finish':
        handle_finish_experiment(args)
    elif args.command == 'result':
        handle_get_result(args)
    elif args.command == 'status':
        handle_get_status(args)
    elif args.command == 'list':
        handle_list_experiments(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main() 