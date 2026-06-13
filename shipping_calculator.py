"""
快递运费计算服务
- 根据目的地、实际重量、体积（长宽高）计算运费
- 体积重 = 长(cm) × 宽(cm) × 高(cm) / 体积系数
- 计费重量 = max(实际重量, 体积重)
- 按区域首重 + 续重方式计费
"""

import math
from dataclasses import dataclass
from typing import Dict, Optional


EXPRESS_COMPANIES: Dict[str, Dict] = {
    "顺丰": {"name": "顺丰速运", "volume_factor": 6000},
    "德邦": {"name": "德邦快递", "volume_factor": 5000},
    "中通": {"name": "中通快递", "volume_factor": 6000},
    "圆通": {"name": "圆通速递", "volume_factor": 6000},
    "申通": {"name": "申通快递", "volume_factor": 6000},
    "京东": {"name": "京东物流", "volume_factor": 6000},
    "极兔": {"name": "极兔速递", "volume_factor": 6000},
    "EMS": {"name": "EMS", "volume_factor": 6000},
}

DEFAULT_COMPANY = "顺丰"
VOLUME_FACTOR = EXPRESS_COMPANIES[DEFAULT_COMPANY]["volume_factor"]


@dataclass
class Package:
    length: float
    width: float
    height: float
    weight: float

    def volume_weight(self, factor: int = VOLUME_FACTOR) -> float:
        if self.length <= 0 or self.width <= 0 or self.height <= 0:
            raise ValueError("长宽高必须为正数")
        return (self.length * self.width * self.height) / factor

    def chargeable_weight(self, factor: int = VOLUME_FACTOR) -> float:
        if self.weight <= 0:
            raise ValueError("实际重量必须为正数")
        return max(self.weight, self.volume_weight(factor))


ZONE_RATES: Dict[str, Dict[str, float]] = {
    "本地": {"zone": "本地", "first_weight": 8.0, "first_kg": 1.0, "additional_per_kg": 2.0},
    "省内": {"zone": "省内", "first_weight": 12.0, "first_kg": 1.0, "additional_per_kg": 3.0},
    "华东": {"zone": "华东", "first_weight": 15.0, "first_kg": 1.0, "additional_per_kg": 5.0},
    "华北": {"zone": "华北", "first_weight": 18.0, "first_kg": 1.0, "additional_per_kg": 6.0},
    "华中": {"zone": "华中", "first_weight": 16.0, "first_kg": 1.0, "additional_per_kg": 5.5},
    "华南": {"zone": "华南", "first_weight": 16.0, "first_kg": 1.0, "additional_per_kg": 5.5},
    "西南": {"zone": "西南", "first_weight": 20.0, "first_kg": 1.0, "additional_per_kg": 7.0},
    "西北": {"zone": "西北", "first_weight": 22.0, "first_kg": 1.0, "additional_per_kg": 8.0},
    "东北": {"zone": "东北", "first_weight": 20.0, "first_kg": 1.0, "additional_per_kg": 7.5},
    "新疆西藏": {"zone": "新疆西藏", "first_weight": 30.0, "first_kg": 1.0, "additional_per_kg": 15.0},
    "港澳台": {"zone": "港澳台", "first_weight": 35.0, "first_kg": 0.5, "additional_per_kg": 20.0},
    "国际-东南亚": {"zone": "国际-东南亚", "first_weight": 50.0, "first_kg": 0.5, "additional_per_kg": 30.0},
    "国际-欧美": {"zone": "国际-欧美", "first_weight": 80.0, "first_kg": 0.5, "additional_per_kg": 50.0},
}

CITY_TO_ZONE: Dict[str, str] = {
    "北京": "华北", "天津": "华北", "河北": "华北", "山西": "华北", "内蒙古": "华北",
    "上海": "华东", "江苏": "华东", "浙江": "华东", "安徽": "华东", "福建": "华东", "江西": "华东", "山东": "华东",
    "广东": "华南", "广西": "华南", "海南": "华南",
    "湖北": "华中", "湖南": "华中", "河南": "华中",
    "重庆": "西南", "四川": "西南", "贵州": "西南", "云南": "西南", "西藏": "新疆西藏",
    "陕西": "西北", "甘肃": "西北", "青海": "西北", "宁夏": "西北", "新疆": "新疆西藏",
    "辽宁": "东北", "吉林": "东北", "黑龙江": "东北",
    "香港": "港澳台", "澳门": "港澳台", "台湾": "港澳台",
}


class ShippingCalculator:
    def __init__(self, volume_factor: int = VOLUME_FACTOR, company: str = DEFAULT_COMPANY):
        self.company = company
        self.volume_factor = volume_factor

    @classmethod
    def for_company(cls, company: str) -> "ShippingCalculator":
        if company not in EXPRESS_COMPANIES:
            raise ValueError(
                f"不支持的快递公司: {company}。支持的公司: {list(EXPRESS_COMPANIES.keys())}"
            )
        return cls(
            volume_factor=EXPRESS_COMPANIES[company]["volume_factor"],
            company=company,
        )

    def resolve_zone(self, destination: str) -> Optional[str]:
        if destination in ZONE_RATES:
            return destination
        if destination in CITY_TO_ZONE:
            return CITY_TO_ZONE[destination]
        for zone in ZONE_RATES:
            if destination.startswith(zone) or zone.startswith(destination):
                return zone
        return None

    def calculate(
        self,
        destination: str,
        length: float,
        width: float,
        height: float,
        weight: float,
    ) -> Dict:
        zone = self.resolve_zone(destination)
        if zone is None:
            raise ValueError(f"不支持的目的地: {destination}")

        package = Package(length=length, width=width, height=height, weight=weight)
        volume_w = package.volume_weight(self.volume_factor)
        chargeable_w = package.chargeable_weight(self.volume_factor)

        rates = ZONE_RATES[zone]
        first_kg = rates["first_kg"]
        first_weight_cost = rates["first_weight"]
        additional_per_kg = rates["additional_per_kg"]

        if chargeable_w <= first_kg:
            total_cost = first_weight_cost
        else:
            remaining_kg = chargeable_w - first_kg
            additional_units = remaining_kg / 0.5 if zone == "港澳台" or zone.startswith("国际") else remaining_kg
            additional_units = math.ceil(additional_units)
            unit_weight = 0.5 if zone == "港澳台" or zone.startswith("国际") else 1.0
            total_cost = first_weight_cost + additional_units * additional_per_kg * unit_weight

        total_cost = round(total_cost, 2)

        return {
            "company": self.company,
            "company_name": EXPRESS_COMPANIES.get(self.company, {}).get("name", self.company),
            "volume_factor": self.volume_factor,
            "destination": destination,
            "zone": zone,
            "package": {
                "length_cm": length,
                "width_cm": width,
                "height_cm": height,
                "actual_weight_kg": weight,
                "volume_weight_kg": round(volume_w, 4),
                "chargeable_weight_kg": round(chargeable_w, 4),
            },
            "rate": {
                "first_weight": first_weight_cost,
                "first_kg": first_kg,
                "additional_per_kg": additional_per_kg,
            },
            "total_cost": total_cost,
        }


def main():
    examples = [
        ("上海", 30, 20, 10, 2),
        ("北京", 50, 40, 30, 3),
        ("新疆", 40, 30, 25, 5),
        ("香港", 25, 20, 15, 1.2),
        ("国际-欧美", 60, 40, 30, 8),
        ("本地", 20, 15, 10, 0.8),
    ]

    print("=" * 80)
    print("快递运费计算服务 - 示例")
    print("=" * 80)

    print(f"\n{'='*40}")
    print("对比: 顺丰 vs 德邦 (体积重系数差异)")
    print(f"{'='*40}")
    compare_cases = [
        (50, 40, 30, 3, "北京"),
        (60, 50, 40, 8, "上海"),
    ]
    for l, w, h, wt, dest in compare_cases:
        print(f"\n包裹: {l}×{w}×{h} cm, 实际重量 {wt} kg, 目的地 {dest}")
        print(f"  体积: {l*w*h:.0f} cm³")
        for company_name in ["顺丰", "德邦"]:
            calc = ShippingCalculator.for_company(company_name)
            result = calc.calculate(dest, l, w, h, wt)
            vf = result["volume_factor"]
            vw = result["package"]["volume_weight_kg"]
            cw = result["package"]["chargeable_weight_kg"]
            print(f"  {company_name}(系数{vf}): 体积重={vw}kg, 计费重={cw}kg, 运费=¥{result['total_cost']}")

    for company_name in ["顺丰", "德邦"]:
        print(f"\n{'='*40}")
        print(f"快递公司: {company_name} (体积重系数: {EXPRESS_COMPANIES[company_name]['volume_factor']})")
        print(f"{'='*40}")
        calc = ShippingCalculator.for_company(company_name)
        for dest, l, w, h, wt in examples:
            try:
                result = calc.calculate(dest, l, w, h, wt)
                print(f"\n目的地: {dest}  |  区域: {result['zone']}")
                print(f"  尺寸: {l}×{w}×{h} cm  |  体积: {l*w*h:.0f} cm³")
                print(f"  实际重量: {wt} kg  |  体积重: {result['package']['volume_weight_kg']} kg")
                print(f"  计费重量: {result['package']['chargeable_weight_kg']} kg")
                print(f"  首重: {result['rate']['first_weight']}元/{result['rate']['first_kg']}kg  |  续重: {result['rate']['additional_per_kg']}元/kg")
                print(f"  总运费: ¥{result['total_cost']}")
            except ValueError as e:
                print(f"\n目的地: {dest} - 错误: {e}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
