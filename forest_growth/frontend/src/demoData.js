// 由 scripts/build_demo_data.py 自动生成（与后端共用 core 计算逻辑）
// 仅在 DRF 后端不可达时用于界面演示；正式数据以 /api 为准。
const demoData = {
  "survey_t1": "T1-2019",
  "survey_t2": "T2-2024",
  "release_id": "eq-2015-v1",
  "population": {
    "totals_kg": {
      "growth_kg_ha": 109808.25030959529,
      "mortality_kg_ha": 471008.3481069016,
      "ingrowth_kg_ha": 22722.105950527486
    },
    "se_kg": {
      "growth_kg_ha": 22989.28330248147,
      "mortality_kg_ha": 140126.15353145107,
      "ingrowth_kg_ha": 5311.368626684881
    },
    "ci95_kg": {
      "growth_kg_ha": [
        10893.347753189795,
        208723.15286600078
      ],
      "mortality_kg_ha": [
        -131905.8288944877,
        1073922.5251082908
      ],
      "ingrowth_kg_ha": [
        -130.86876978383225,
        45575.080670838805
      ]
    },
    "degrees_of_freedom": {
      "growth_kg_ha": 2,
      "mortality_kg_ha": 2,
      "ingrowth_kg_ha": 2
    },
    "method": "stratified_design_weighted",
    "source": {
      "estimator": "Ŷ = Σ_h A_h · mean_i(y_ha,i);  y_ha,i = Σ_tree / area_i",
      "stratum_areas_ha": {
        "H1": 120.0,
        "H2": 80.0
      },
      "n_plots": 4,
      "weighting": "样地等概率，无单木不等概权重"
    },
    "uncertainty": {
      "sampling": "分层估计，层内样地间方差/n_h，按 A_h² 汇总",
      "confidence": 0.95,
      "undetermined_strata": [],
      "note": "仅 1 个样地的层无法估计层内方差，SE/CI 记为 NaN 而非 0；测量误差与方程残差 CV 在样地分量 uncertainty 中给出，需要联合传播时在分析运行中显式开启"
    }
  },
  "plots": [
    {
      "plot_id": "P01",
      "stratum_id": "H1",
      "area_ha": 0.06,
      "growth": {
        "component": "growth",
        "n_trees": 5,
        "biomass_kg": 48.039112271159965,
        "biomass_kg_per_ha": 800.6518711859994,
        "mean_dbh_increment_cm": 0.7400000000000002,
        "source": {
          "release_id": "eq-2015-v1",
          "biomass_component": "agb_oven_dry_kg",
          "plot_id": "P01",
          "area_ha": 0.06,
          "measurement_units": {
            "dbh": "cm",
            "height": "m",
            "biomass": "kg"
          },
          "tree_tags": [
            "P01-104",
            "P01-001",
            "P01-002",
            "P01-003",
            "P01-006",
            "P01-008"
          ],
          "kind": "两期实测胸径 + 异速方程推算两期生物量之差",
          "zero_growth_tags": [
            "P01-003"
          ]
        },
        "uncertainty": {
          "sampling": "样地层面方差在总体加权阶段估计",
          "measurement": {
            "dbh_sd_cm": 0.3,
            "height_sd_m": 0.5,
            "zero_growth_epsilon_cm": 0.3
          },
          "equation_mean_cv": 0.170182255244194,
          "missing_treatment": "完整木分析（complete-case）：缺测木不插补、不计零，从生长均值中剔除；最坏情形见 uncertainty.missing_bounds",
          "n_missing": 1
        }
      },
      "mortality": {
        "component": "mortality",
        "n_trees": 1,
        "biomass_kg": 272.14809385388804,
        "biomass_kg_per_ha": 4535.801564231468,
        "mean_dbh_increment_cm": null,
        "source": {
          "release_id": "eq-2015-v1",
          "biomass_component": "agb_oven_dry_kg",
          "plot_id": "P01",
          "area_ha": 0.06,
          "measurement_units": {
            "dbh": "cm",
            "height": "m",
            "biomass": "kg"
          },
          "tree_tags": [
            "P01-005"
          ],
          "kind": "t2 确认死亡（伐桩/枯立），生物量取 t1 实测胸径推算"
        },
        "uncertainty": {
          "sampling": "样地层面方差在总体加权阶段估计",
          "measurement": {
            "dbh_sd_cm": 0.3
          },
          "equation_mean_cv": 0.15146286673637205,
          "missing_treatment": "只有 t2 未见、无死亡证据的个体记为缺测而非死亡"
        }
      },
      "ingrowth": {
        "component": "ingrowth",
        "n_trees": 1,
        "biomass_kg": 8.421781565400634,
        "biomass_kg_per_ha": 140.36302609001058,
        "mean_dbh_increment_cm": null,
        "source": {
          "release_id": "eq-2015-v1",
          "biomass_component": "agb_oven_dry_kg",
          "plot_id": "P01",
          "area_ha": 0.06,
          "measurement_units": {
            "dbh": "cm",
            "height": "m",
            "biomass": "kg"
          },
          "tree_tags": [
            "P01-201"
          ],
          "kind": "t2 新出现且胸径 >= 5.0 cm，生物量取 t2 实测胸径推算"
        },
        "uncertainty": {
          "sampling": "样地层面方差在总体加权阶段估计",
          "measurement": {
            "dbh_sd_cm": 0.3
          },
          "equation_mean_cv": 0.18159295140505866,
          "missing_treatment": "未达起测径阶个体单列，不计入进界"
        }
      },
      "zero_growth_tags": [
        "P01-003"
      ],
      "negative_growth_tags": [],
      "missing_measurement_tags": [
        "P01-006"
      ],
      "unresolved_tags": [
        "P01-007"
      ],
      "balance_check": {
        "b1_kg_resolved": 715.1814148173277,
        "b2_kg_resolved": 499.4942148000002,
        "expected_b2_kg": 499.49421480000024,
        "residual_kg": -5.684341886080802e-14,
        "note": "残差应≈0；不为零说明有缺测/未决个体被排除在分量外"
      },
      "pairs": [
        {
          "status": "survivor",
          "tag_t1": "P01-004",
          "tag_t2": "P01-104",
          "distance_m": 0.05385164807134554,
          "matched_via": "crosswalk",
          "note": "",
          "t1": {
            "tag": "P01-004",
            "species": "PIMA",
            "status": "alive",
            "x_m": 16.0,
            "y_m": 9.0,
            "dbh_cm": 20.0,
            "height_m": 14.0,
            "remark": ""
          },
          "t2": {
            "tag": "P01-104",
            "species": "PIMA",
            "status": "alive",
            "x_m": 16.05,
            "y_m": 9.02,
            "dbh_cm": 21.2,
            "height_m": 14.6,
            "remark": ""
          }
        },
        {
          "status": "survivor",
          "tag_t1": "P01-001",
          "tag_t2": "P01-001",
          "distance_m": 0.05385164807134472,
          "matched_via": "tag",
          "note": "",
          "t1": {
            "tag": "P01-001",
            "species": "PIMA",
            "status": "alive",
            "x_m": 5.0,
            "y_m": 5.0,
            "dbh_cm": 12.0,
            "height_m": 9.0,
            "remark": ""
          },
          "t2": {
            "tag": "P01-001",
            "species": "PIMA",
            "status": "alive",
            "x_m": 5.05,
            "y_m": 5.02,
            "dbh_cm": 12.8,
            "height_m": 9.4,
            "remark": ""
          }
        },
        {
          "status": "survivor",
          "tag_t1": "P01-002",
          "tag_t2": "P01-002",
          "distance_m": 0.04999999999999982,
          "matched_via": "tag",
          "note": "",
          "t1": {
            "tag": "P01-002",
            "species": "PIMA",
            "status": "alive",
            "x_m": 8.0,
            "y_m": 3.0,
            "dbh_cm": 14.5,
            "height_m": 10.5,
            "remark": ""
          },
          "t2": {
            "tag": "P01-002",
            "species": "PIMA",
            "status": "alive",
            "x_m": 8.0,
            "y_m": 3.05,
            "dbh_cm": 15.3,
            "height_m": 11.0,
            "remark": ""
          }
        },
        {
          "status": "survivor",
          "tag_t1": "P01-003",
          "tag_t2": "P01-003",
          "distance_m": 0.0,
          "matched_via": "tag",
          "note": "",
          "t1": {
            "tag": "P01-003",
            "species": "CULA",
            "status": "alive",
            "x_m": 12.0,
            "y_m": 7.0,
            "dbh_cm": 18.0,
            "height_m": 13.0,
            "remark": ""
          },
          "t2": {
            "tag": "P01-003",
            "species": "CULA",
            "status": "alive",
            "x_m": 12.0,
            "y_m": 7.0,
            "dbh_cm": 18.1,
            "height_m": 13.1,
            "remark": ""
          }
        },
        {
          "status": "mortality",
          "tag_t1": "P01-005",
          "tag_t2": "P01-005",
          "distance_m": 0.0,
          "matched_via": "tag",
          "note": "t1 存活、t2 确认死亡（伐桩/枯立木）",
          "t1": {
            "tag": "P01-005",
            "species": "CULA",
            "status": "alive",
            "x_m": 20.0,
            "y_m": 12.0,
            "dbh_cm": 22.0,
            "height_m": 15.0,
            "remark": ""
          },
          "t2": {
            "tag": "P01-005",
            "species": "CULA",
            "status": "dead",
            "x_m": 20.0,
            "y_m": 12.0,
            "dbh_cm": null,
            "height_m": null,
            "remark": "伐桩，确认死亡"
          }
        },
        {
          "status": "survivor",
          "tag_t1": "P01-006",
          "tag_t2": "P01-006",
          "distance_m": 0.0,
          "matched_via": "tag",
          "note": "",
          "t1": {
            "tag": "P01-006",
            "species": "PIMA",
            "status": "alive",
            "x_m": 22.0,
            "y_m": 15.0,
            "dbh_cm": 24.0,
            "height_m": 16.0,
            "remark": ""
          },
          "t2": {
            "tag": "P01-006",
            "species": "PIMA",
            "status": "alive",
            "x_m": 22.0,
            "y_m": 15.0,
            "dbh_cm": null,
            "height_m": null,
            "remark": "胸径漏测"
          }
        },
        {
          "status": "unresolved_location_conflict",
          "tag_t1": "P01-007",
          "tag_t2": "P01-007",
          "distance_m": 24.08318915758459,
          "matched_via": "tag",
          "note": "同号 P01-007 但位置相差 24.08 m > 容差 1.0 m，可能是重号/补号，禁止自动合并",
          "t1": {
            "tag": "P01-007",
            "species": "PIMA",
            "status": "alive",
            "x_m": 3.0,
            "y_m": 20.0,
            "dbh_cm": 16.2,
            "height_m": 11.0,
            "remark": ""
          },
          "t2": {
            "tag": "P01-007",
            "species": "PIMA",
            "status": "alive",
            "x_m": 21.0,
            "y_m": 4.0,
            "dbh_cm": 17.0,
            "height_m": 12.0,
            "remark": "编号漆字模糊，疑似补号"
          }
        },
        {
          "status": "survivor",
          "tag_t1": "P01-008",
          "tag_t2": "P01-008",
          "distance_m": 0.019999999999999574,
          "matched_via": "tag",
          "note": "",
          "t1": {
            "tag": "P01-008",
            "species": "CULA",
            "status": "alive",
            "x_m": 25.0,
            "y_m": 6.0,
            "dbh_cm": 10.0,
            "height_m": 8.0,
            "remark": ""
          },
          "t2": {
            "tag": "P01-008",
            "species": "CULA",
            "status": "alive",
            "x_m": 25.0,
            "y_m": 6.02,
            "dbh_cm": 10.9,
            "height_m": 8.5,
            "remark": ""
          }
        },
        {
          "status": "ingrowth",
          "tag_t1": null,
          "tag_t2": "P01-201",
          "distance_m": null,
          "matched_via": "none",
          "note": "t2 新进界木，胸径 6.2 cm >= 5.0 cm",
          "t1": null,
          "t2": {
            "tag": "P01-201",
            "species": "PIMA",
            "status": "alive",
            "x_m": 10.0,
            "y_m": 18.0,
            "dbh_cm": 6.2,
            "height_m": 4.5,
            "remark": ""
          }
        },
        {
          "status": "below_threshold_t2",
          "tag_t1": null,
          "tag_t2": "P01-202",
          "distance_m": null,
          "matched_via": "none",
          "note": "t2 测到但未达起测胸径，不计进界",
          "t1": null,
          "t2": {
            "tag": "P01-202",
            "species": "CULA",
            "status": "alive",
            "x_m": 14.0,
            "y_m": 2.0,
            "dbh_cm": 3.4,
            "height_m": 2.6,
            "remark": ""
          }
        }
      ]
    },
    {
      "plot_id": "P02",
      "stratum_id": "H1",
      "area_ha": 0.08,
      "growth": {
        "component": "growth",
        "n_trees": 2,
        "biomass_kg": 36.22544623357564,
        "biomass_kg_per_ha": 452.8180779196955,
        "mean_dbh_increment_cm": 1.1000000000000014,
        "source": {
          "release_id": "eq-2015-v1",
          "biomass_component": "agb_oven_dry_kg",
          "plot_id": "P02",
          "area_ha": 0.08,
          "measurement_units": {
            "dbh": "cm",
            "height": "m",
            "biomass": "kg"
          },
          "tree_tags": [
            "P02-001",
            "P02-003"
          ],
          "kind": "两期实测胸径 + 异速方程推算两期生物量之差",
          "zero_growth_tags": []
        },
        "uncertainty": {
          "sampling": "样地层面方差在总体加权阶段估计",
          "measurement": {
            "dbh_sd_cm": 0.3,
            "height_sd_m": 0.5,
            "zero_growth_epsilon_cm": 0.3
          },
          "equation_mean_cv": 0.18159295140505866,
          "missing_treatment": "完整木分析（complete-case）：缺测木不插补、不计零，从生长均值中剔除；最坏情形见 uncertainty.missing_bounds",
          "n_missing": 0
        }
      },
      "mortality": {
        "component": "mortality",
        "n_trees": 1,
        "biomass_kg": 191.2599922802158,
        "biomass_kg_per_ha": 2390.7499035026976,
        "mean_dbh_increment_cm": null,
        "source": {
          "release_id": "eq-2015-v1",
          "biomass_component": "agb_oven_dry_kg",
          "plot_id": "P02",
          "area_ha": 0.08,
          "measurement_units": {
            "dbh": "cm",
            "height": "m",
            "biomass": "kg"
          },
          "tree_tags": [
            "P02-002"
          ],
          "kind": "t2 确认死亡（伐桩/枯立），生物量取 t1 实测胸径推算"
        },
        "uncertainty": {
          "sampling": "样地层面方差在总体加权阶段估计",
          "measurement": {
            "dbh_sd_cm": 0.3
          },
          "equation_mean_cv": 0.15146286673637205,
          "missing_treatment": "只有 t2 未见、无死亡证据的个体记为缺测而非死亡"
        }
      },
      "ingrowth": {
        "component": "ingrowth",
        "n_trees": 1,
        "biomass_kg": 12.030806327797519,
        "biomass_kg_per_ha": 150.38507909746897,
        "mean_dbh_increment_cm": null,
        "source": {
          "release_id": "eq-2015-v1",
          "biomass_component": "agb_oven_dry_kg",
          "plot_id": "P02",
          "area_ha": 0.08,
          "measurement_units": {
            "dbh": "cm",
            "height": "m",
            "biomass": "kg"
          },
          "tree_tags": [
            "P02-101"
          ],
          "kind": "t2 新出现且胸径 >= 5.0 cm，生物量取 t2 实测胸径推算"
        },
        "uncertainty": {
          "sampling": "样地层面方差在总体加权阶段估计",
          "measurement": {
            "dbh_sd_cm": 0.3
          },
          "equation_mean_cv": 0.15146286673637205,
          "missing_treatment": "未达起测径阶个体单列，不计入进界"
        }
      },
      "zero_growth_tags": [],
      "negative_growth_tags": [],
      "missing_measurement_tags": [],
      "unresolved_tags": [],
      "balance_check": {
        "b1_kg_resolved": 457.25035142128274,
        "b2_kg_resolved": 314.2466117024401,
        "expected_b2_kg": 314.24661170244013,
        "residual_kg": -5.684341886080802e-14,
        "note": "残差应≈0；不为零说明有缺测/未决个体被排除在分量外"
      },
      "pairs": [
        {
          "status": "survivor",
          "tag_t1": "P02-001",
          "tag_t2": "P02-001",
          "distance_m": 0.04999999999999982,
          "matched_via": "tag",
          "note": "",
          "t1": {
            "tag": "P02-001",
            "species": "PIMA",
            "status": "alive",
            "x_m": 4.0,
            "y_m": 4.0,
            "dbh_cm": 15.0,
            "height_m": 11.0,
            "remark": ""
          },
          "t2": {
            "tag": "P02-001",
            "species": "PIMA",
            "status": "alive",
            "x_m": 4.05,
            "y_m": 4.0,
            "dbh_cm": 16.1,
            "height_m": 11.6,
            "remark": ""
          }
        },
        {
          "status": "mortality",
          "tag_t1": "P02-002",
          "tag_t2": "P02-002",
          "distance_m": 0.0,
          "matched_via": "tag",
          "note": "t1 存活、t2 确认死亡（伐桩/枯立木）",
          "t1": {
            "tag": "P02-002",
            "species": "CULA",
            "status": "alive",
            "x_m": 9.0,
            "y_m": 9.0,
            "dbh_cm": 19.0,
            "height_m": 14.0,
            "remark": ""
          },
          "t2": {
            "tag": "P02-002",
            "species": "CULA",
            "status": "dead",
            "x_m": 9.0,
            "y_m": 9.0,
            "dbh_cm": null,
            "height_m": null,
            "remark": "枯立木"
          }
        },
        {
          "status": "survivor",
          "tag_t1": "P02-003",
          "tag_t2": "P02-003",
          "distance_m": 0.028284271247461613,
          "matched_via": "tag",
          "note": "",
          "t1": {
            "tag": "P02-003",
            "species": "PIMA",
            "status": "alive",
            "x_m": 14.0,
            "y_m": 3.0,
            "dbh_cm": 23.0,
            "height_m": 16.5,
            "remark": ""
          },
          "t2": {
            "tag": "P02-003",
            "species": "PIMA",
            "status": "alive",
            "x_m": 14.02,
            "y_m": 3.02,
            "dbh_cm": 24.1,
            "height_m": 17.0,
            "remark": ""
          }
        },
        {
          "status": "ingrowth",
          "tag_t1": null,
          "tag_t2": "P02-101",
          "distance_m": null,
          "matched_via": "none",
          "note": "t2 新进界木，胸径 7.0 cm >= 5.0 cm",
          "t1": null,
          "t2": {
            "tag": "P02-101",
            "species": "CULA",
            "status": "alive",
            "x_m": 20.0,
            "y_m": 20.0,
            "dbh_cm": 7.0,
            "height_m": 5.0,
            "remark": ""
          }
        }
      ]
    },
    {
      "plot_id": "P03",
      "stratum_id": "H2",
      "area_ha": 0.05,
      "growth": {
        "component": "growth",
        "n_trees": 2,
        "biomass_kg": 27.650665285466793,
        "biomass_kg_per_ha": 553.0133057093358,
        "mean_dbh_increment_cm": 1.0999999999999996,
        "source": {
          "release_id": "eq-2015-v1",
          "biomass_component": "agb_oven_dry_kg",
          "plot_id": "P03",
          "area_ha": 0.05,
          "measurement_units": {
            "dbh": "cm",
            "height": "m",
            "biomass": "kg"
          },
          "tree_tags": [
            "P03-001",
            "P03-002"
          ],
          "kind": "两期实测胸径 + 异速方程推算两期生物量之差",
          "zero_growth_tags": []
        },
        "uncertainty": {
          "sampling": "样地层面方差在总体加权阶段估计",
          "measurement": {
            "dbh_sd_cm": 0.3,
            "height_sd_m": 0.5,
            "zero_growth_epsilon_cm": 0.3
          },
          "equation_mean_cv": 0.16720795435624466,
          "missing_treatment": "完整木分析（complete-case）：缺测木不插补、不计零，从生长均值中剔除；最坏情形见 uncertainty.missing_bounds",
          "n_missing": 0
        }
      },
      "mortality": {
        "component": "mortality",
        "n_trees": 0,
        "biomass_kg": 0.0,
        "biomass_kg_per_ha": 0.0,
        "mean_dbh_increment_cm": null,
        "source": {
          "release_id": "eq-2015-v1",
          "biomass_component": "agb_oven_dry_kg",
          "plot_id": "P03",
          "area_ha": 0.05,
          "measurement_units": {
            "dbh": "cm",
            "height": "m",
            "biomass": "kg"
          },
          "tree_tags": [],
          "kind": "t2 确认死亡（伐桩/枯立），生物量取 t1 实测胸径推算"
        },
        "uncertainty": {
          "sampling": "样地层面方差在总体加权阶段估计",
          "measurement": {
            "dbh_sd_cm": 0.3
          },
          "equation_mean_cv": null,
          "missing_treatment": "只有 t2 未见、无死亡证据的个体记为缺测而非死亡"
        }
      },
      "ingrowth": {
        "component": "ingrowth",
        "n_trees": 1,
        "biomass_kg": 6.59652454909839,
        "biomass_kg_per_ha": 131.9304909819678,
        "mean_dbh_increment_cm": null,
        "source": {
          "release_id": "eq-2015-v1",
          "biomass_component": "agb_oven_dry_kg",
          "plot_id": "P03",
          "area_ha": 0.05,
          "measurement_units": {
            "dbh": "cm",
            "height": "m",
            "biomass": "kg"
          },
          "tree_tags": [
            "P03-101"
          ],
          "kind": "t2 新出现且胸径 >= 5.0 cm，生物量取 t2 实测胸径推算"
        },
        "uncertainty": {
          "sampling": "样地层面方差在总体加权阶段估计",
          "measurement": {
            "dbh_sd_cm": 0.3
          },
          "equation_mean_cv": 0.18159295140505866,
          "missing_treatment": "未达起测径阶个体单列，不计入进界"
        }
      },
      "zero_growth_tags": [],
      "negative_growth_tags": [],
      "missing_measurement_tags": [],
      "unresolved_tags": [],
      "balance_check": {
        "b1_kg_resolved": 138.66928164735657,
        "b2_kg_resolved": 172.91647148192175,
        "expected_b2_kg": 172.91647148192175,
        "residual_kg": 0.0,
        "note": "残差应≈0；不为零说明有缺测/未决个体被排除在分量外"
      },
      "pairs": [
        {
          "status": "survivor",
          "tag_t1": "P03-001",
          "tag_t2": "P03-001",
          "distance_m": 0.020000000000000018,
          "matched_via": "tag",
          "note": "",
          "t1": {
            "tag": "P03-001",
            "species": "CULA",
            "status": "alive",
            "x_m": 2.0,
            "y_m": 2.0,
            "dbh_cm": 11.0,
            "height_m": 8.5,
            "remark": ""
          },
          "t2": {
            "tag": "P03-001",
            "species": "CULA",
            "status": "alive",
            "x_m": 2.0,
            "y_m": 2.02,
            "dbh_cm": 12.0,
            "height_m": 9.0,
            "remark": ""
          }
        },
        {
          "status": "survivor",
          "tag_t1": "P03-002",
          "tag_t2": "P03-002",
          "distance_m": 0.019999999999999574,
          "matched_via": "tag",
          "note": "",
          "t1": {
            "tag": "P03-002",
            "species": "PIMA",
            "status": "alive",
            "x_m": 7.0,
            "y_m": 6.0,
            "dbh_cm": 17.0,
            "height_m": 12.0,
            "remark": ""
          },
          "t2": {
            "tag": "P03-002",
            "species": "PIMA",
            "status": "alive",
            "x_m": 7.02,
            "y_m": 6.0,
            "dbh_cm": 18.2,
            "height_m": 12.6,
            "remark": ""
          }
        },
        {
          "status": "ingrowth",
          "tag_t1": null,
          "tag_t2": "P03-101",
          "distance_m": null,
          "matched_via": "none",
          "note": "t2 新进界木，胸径 5.6 cm >= 5.0 cm",
          "t1": null,
          "t2": {
            "tag": "P03-101",
            "species": "PIMA",
            "status": "alive",
            "x_m": 11.0,
            "y_m": 10.0,
            "dbh_cm": 5.6,
            "height_m": 4.0,
            "remark": ""
          }
        }
      ]
    },
    {
      "plot_id": "P04",
      "stratum_id": "H2",
      "area_ha": 0.05,
      "growth": {
        "component": "growth",
        "n_trees": 1,
        "biomass_kg": 15.599401418600195,
        "biomass_kg_per_ha": 311.9880283720039,
        "mean_dbh_increment_cm": 0.8999999999999986,
        "source": {
          "release_id": "eq-2015-v1",
          "biomass_component": "agb_oven_dry_kg",
          "plot_id": "P04",
          "area_ha": 0.05,
          "measurement_units": {
            "dbh": "cm",
            "height": "m",
            "biomass": "kg"
          },
          "tree_tags": [
            "P04-001"
          ],
          "kind": "两期实测胸径 + 异速方程推算两期生物量之差",
          "zero_growth_tags": []
        },
        "uncertainty": {
          "sampling": "样地层面方差在总体加权阶段估计",
          "measurement": {
            "dbh_sd_cm": 0.3,
            "height_sd_m": 0.5,
            "zero_growth_epsilon_cm": 0.3
          },
          "equation_mean_cv": 0.18159295140505866,
          "missing_treatment": "完整木分析（complete-case）：缺测木不插补、不计零，从生长均值中剔除；最坏情形见 uncertainty.missing_bounds",
          "n_missing": 0
        }
      },
      "mortality": {
        "component": "mortality",
        "n_trees": 1,
        "biomass_kg": 69.26907505356466,
        "biomass_kg_per_ha": 1385.381501071293,
        "mean_dbh_increment_cm": null,
        "source": {
          "release_id": "eq-2015-v1",
          "biomass_component": "agb_oven_dry_kg",
          "plot_id": "P04",
          "area_ha": 0.05,
          "measurement_units": {
            "dbh": "cm",
            "height": "m",
            "biomass": "kg"
          },
          "tree_tags": [
            "P04-002"
          ],
          "kind": "t2 确认死亡（伐桩/枯立），生物量取 t1 实测胸径推算"
        },
        "uncertainty": {
          "sampling": "样地层面方差在总体加权阶段估计",
          "measurement": {
            "dbh_sd_cm": 0.3
          },
          "equation_mean_cv": 0.15146286673637205,
          "missing_treatment": "只有 t2 未见、无死亡证据的个体记为缺测而非死亡"
        }
      },
      "ingrowth": {
        "component": "ingrowth",
        "n_trees": 0,
        "biomass_kg": 0.0,
        "biomass_kg_per_ha": 0.0,
        "mean_dbh_increment_cm": null,
        "source": {
          "release_id": "eq-2015-v1",
          "biomass_component": "agb_oven_dry_kg",
          "plot_id": "P04",
          "area_ha": 0.05,
          "measurement_units": {
            "dbh": "cm",
            "height": "m",
            "biomass": "kg"
          },
          "tree_tags": [],
          "kind": "t2 新出现且胸径 >= 5.0 cm，生物量取 t2 实测胸径推算"
        },
        "uncertainty": {
          "sampling": "样地层面方差在总体加权阶段估计",
          "measurement": {
            "dbh_sd_cm": 0.3
          },
          "equation_mean_cv": null,
          "missing_treatment": "未达起测径阶个体单列，不计入进界"
        }
      },
      "zero_growth_tags": [],
      "negative_growth_tags": [],
      "missing_measurement_tags": [],
      "unresolved_tags": [],
      "balance_check": {
        "b1_kg_resolved": 209.2716127460057,
        "b2_kg_resolved": 155.60193911104122,
        "expected_b2_kg": 155.60193911104125,
        "residual_kg": -2.842170943040401e-14,
        "note": "残差应≈0；不为零说明有缺测/未决个体被排除在分量外"
      },
      "pairs": [
        {
          "status": "survivor",
          "tag_t1": "P04-001",
          "tag_t2": "P04-001",
          "distance_m": 0.020000000000000018,
          "matched_via": "tag",
          "note": "",
          "t1": {
            "tag": "P04-001",
            "species": "PIMA",
            "status": "alive",
            "x_m": 3.0,
            "y_m": 8.0,
            "dbh_cm": 20.0,
            "height_m": 14.0,
            "remark": ""
          },
          "t2": {
            "tag": "P04-001",
            "species": "PIMA",
            "status": "alive",
            "x_m": 3.02,
            "y_m": 8.0,
            "dbh_cm": 20.9,
            "height_m": 14.4,
            "remark": ""
          }
        },
        {
          "status": "mortality",
          "tag_t1": "P04-002",
          "tag_t2": "P04-002",
          "distance_m": 0.0,
          "matched_via": "tag",
          "note": "t1 存活、t2 确认死亡（伐桩/枯立木）",
          "t1": {
            "tag": "P04-002",
            "species": "CULA",
            "status": "alive",
            "x_m": 8.0,
            "y_m": 3.0,
            "dbh_cm": 13.0,
            "height_m": 10.0,
            "remark": ""
          },
          "t2": {
            "tag": "P04-002",
            "species": "CULA",
            "status": "dead",
            "x_m": 8.0,
            "y_m": 3.0,
            "dbh_cm": null,
            "height_m": null,
            "remark": ""
          }
        }
      ]
    }
  ],
  "_plots": [
    {
      "plot_id": "P01",
      "stratum_code": "H1",
      "area_ha": 0.06,
      "boundary": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              117.32,
              26.55
            ],
            [
              117.32020096,
              26.55
            ],
            [
              117.32020096,
              26.55026949
            ],
            [
              117.32,
              26.55026949
            ],
            [
              117.32,
              26.55
            ]
          ]
        ]
      },
      "centroid": {
        "type": "Point",
        "coordinates": [
          117.32,
          26.55
        ]
      }
    },
    {
      "plot_id": "P02",
      "stratum_code": "H1",
      "area_ha": 0.08,
      "boundary": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              117.355,
              26.572
            ],
            [
              117.35520096,
              26.572
            ],
            [
              117.35520096,
              26.57226949
            ],
            [
              117.355,
              26.57226949
            ],
            [
              117.355,
              26.572
            ]
          ]
        ]
      },
      "centroid": {
        "type": "Point",
        "coordinates": [
          117.355,
          26.572
        ]
      }
    },
    {
      "plot_id": "P03",
      "stratum_code": "H2",
      "area_ha": 0.05,
      "boundary": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              117.28,
              26.49
            ],
            [
              117.28020096,
              26.49
            ],
            [
              117.28020096,
              26.49026949
            ],
            [
              117.28,
              26.49026949
            ],
            [
              117.28,
              26.49
            ]
          ]
        ]
      },
      "centroid": {
        "type": "Point",
        "coordinates": [
          117.28,
          26.49
        ]
      }
    },
    {
      "plot_id": "P04",
      "stratum_code": "H2",
      "area_ha": 0.05,
      "boundary": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              117.265,
              26.505
            ],
            [
              117.26520096,
              26.505
            ],
            [
              117.26520096,
              26.50526949
            ],
            [
              117.265,
              26.50526949
            ],
            [
              117.265,
              26.505
            ]
          ]
        ]
      },
      "centroid": {
        "type": "Point",
        "coordinates": [
          117.265,
          26.505
        ]
      }
    }
  ]
};

export default demoData;
