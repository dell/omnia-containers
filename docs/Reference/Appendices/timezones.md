
# Supported Timezone Values


The `timezone` parameter in `provision_config.yml` accepts any valid IANA
timezone string. This page lists commonly used values. For the complete list,
consult the [IANA Time Zone Database](https://www.iana.org/time-zones).

## UTC and special values


| Value | Description |
| --- | --- |
| `UTC` | Coordinated Universal Time. **Default** if `timezone` is not specified. Recommended for clusters spanning multiple geographic locations. |
| `Etc/UTC` | Equivalent to `UTC`. |

## Americas


| Timezone | UTC Offset | Common Name |
| --- | --- | --- |
| `America/New_York` | UTC-5 (EST) / UTC-4 (EDT) | US Eastern |
| `America/Chicago` | UTC-6 (CST) / UTC-5 (CDT) | US Central |
| `America/Denver` | UTC-7 (MST) / UTC-6 (MDT) | US Mountain |
| `America/Los_Angeles` | UTC-8 (PST) / UTC-7 (PDT) | US Pacific |
| `America/Anchorage` | UTC-9 (AKST) / UTC-8 (AKDT) | US Alaska |
| `Pacific/Honolulu` | UTC-10 (HST) | US Hawaii |
| `America/Toronto` | UTC-5 (EST) / UTC-4 (EDT) | Canada Eastern |
| `America/Vancouver` | UTC-8 (PST) / UTC-7 (PDT) | Canada Pacific |
| `America/Sao_Paulo` | UTC-3 (BRT) | Brazil |
| `America/Mexico_City` | UTC-6 (CST) / UTC-5 (CDT) | Mexico Central |
| `America/Argentina/Buenos_Aires` | UTC-3 (ART) | Argentina |

## Europe


| Timezone | UTC Offset | Common Name |
| --- | --- | --- |
| `Europe/London` | UTC+0 (GMT) / UTC+1 (BST) | United Kingdom |
| `Europe/Paris` | UTC+1 (CET) / UTC+2 (CEST) | Central European |
| `Europe/Berlin` | UTC+1 (CET) / UTC+2 (CEST) | Germany |
| `Europe/Amsterdam` | UTC+1 (CET) / UTC+2 (CEST) | Netherlands |
| `Europe/Rome` | UTC+1 (CET) / UTC+2 (CEST) | Italy |
| `Europe/Madrid` | UTC+1 (CET) / UTC+2 (CEST) | Spain |
| `Europe/Moscow` | UTC+3 (MSK) | Russia (Moscow) |
| `Europe/Istanbul` | UTC+3 (TRT) | Turkey |
| `Europe/Helsinki` | UTC+2 (EET) / UTC+3 (EEST) | Finland |
| `Europe/Warsaw` | UTC+1 (CET) / UTC+2 (CEST) | Poland |

## Asia and Pacific


| Timezone | UTC Offset | Common Name |
| --- | --- | --- |
| `Asia/Kolkata` | UTC+5:30 (IST) | India |
| `Asia/Shanghai` | UTC+8 (CST) | China |
| `Asia/Tokyo` | UTC+9 (JST) | Japan |
| `Asia/Seoul` | UTC+9 (KST) | South Korea |
| `Asia/Singapore` | UTC+8 (SGT) | Singapore |
| `Asia/Hong_Kong` | UTC+8 (HKT) | Hong Kong |
| `Asia/Taipei` | UTC+8 (CST) | Taiwan |
| `Asia/Dubai` | UTC+4 (GST) | UAE |
| `Asia/Riyadh` | UTC+3 (AST) | Saudi Arabia |
| `Asia/Jakarta` | UTC+7 (WIB) | Indonesia (Western) |
| `Asia/Bangkok` | UTC+7 (ICT) | Thailand |
| `Asia/Karachi` | UTC+5 (PKT) | Pakistan |
| `Australia/Sydney` | UTC+10 (AEST) / UTC+11 (AEDT) | Australia Eastern |
| `Australia/Perth` | UTC+8 (AWST) | Australia Western |
| `Pacific/Auckland` | UTC+12 (NZST) / UTC+13 (NZDT) | New Zealand |

## Africa and Middle East


| Timezone | UTC Offset | Common Name |
| --- | --- | --- |
| `Africa/Cairo` | UTC+2 (EET) | Egypt |
| `Africa/Lagos` | UTC+1 (WAT) | Nigeria (West Africa) |
| `Africa/Johannesburg` | UTC+2 (SAST) | South Africa |
| `Africa/Nairobi` | UTC+3 (EAT) | Kenya (East Africa) |
| `Africa/Casablanca` | UTC+1 (WEST) | Morocco |

!!! note

    - The timezone is applied to all nodes provisioned by Omnia. To use
      different timezones on different nodes, modify the timezone post-
      provisioning via `timedatectl`.
    - UTC offsets shown are standard time. Daylight saving adjustments are
      handled automatically by the OS.

!!! info

    - [Provision Config](../Configuration/provision_config.md) -- Where `timezone`
      is configured.
