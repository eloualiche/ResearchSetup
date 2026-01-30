
# --------------------------------------------------------------------------------------------------
let
    rules_user = (import "../utilities/config/rules_user_fixed.toml")
in 
let

    ENV = rules_user.env,
    PD = rules_user.PROJECT_DIRS,
    DD = rules_user.DATA_DIRS,
in
# --------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------
let 
# cannot do dynamic imports see https://github.com/tweag/nickel/issues/1865
    link_contracts = (import "../utilities/config/nickel/link_contracts.ncl") 
in
let
    Link = link_contracts.link,
    serialize_records = link_contracts.serialize_records,
    filter_out_not_exported = link_contracts.filter_out_not_exported
in
# --------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------
{

  # -------------------------------------------------------------------------------------------- #
  # -- this is meant to be overriden on evaluation by pwd ...
  env | not_exported = {
    local_task
      | String
      | doc "task"
      | default
      = ".",
  },

  # -------------------------------------------------------------------------------------------- #
  # -- COG STANDARD (from dhall file)
  CoG_INDEMP | Link = 'dir {
        metadata = { description = "Census of Governments IndEmp." },
        source = { directory = "%{DD.CoG_RAW}/IndEmp" },
        target = { directory = "%{env.local_task}/input/CoG_RAW/IndEmp" } },

  CoG_INDFIN | Link = 'dir {
        metadata = { description = "Census of Governments IndFin." },
        source = { directory = "%{DD.CoG_RAW}/IndFin" },
        target = { directory = "%{env.local_task}/input/CoG_RAW/IndFin" } },

  CoG_ASPEP | Link = 'dir {
        metadata = { description = "Census of Governments ASPEP." },
        source = { directory = "%{DD.CoG_RAW}/ASPEP" },
        target = { directory = "%{env.local_task}/input/CoG_RAW/ASPEP" } },

  CoG_QTAX | Link = 'dir {
        metadata = { description = "Census of Governments QTAX." },
        source = { directory = "%{DD.CoG_RAW}/QTAX" },
        target = { directory = "%{env.local_task}/input/CoG_RAW/QTAX" } },

  CoG_ASSLGF | Link = 'dir {
        metadata = { description = "Census of Governments ASSLGF." },
        source = { directory = "%{DD.CoG_RAW}/ASSLGF" },
        target = { directory = "%{env.local_task}/input/CoG_RAW/ASSLGF" } },
  # -------------------------------------------------------------------------------------------- #


  # -------------------------------------------------------------------------------------------- #
  # -- CoG Historical (from the dhall file) 
    CoG_HISTORICAL_STATE_EMP | Link = 'file {
        metadata = { description = "Census of Governments Historical Files: STATES EMPLOYMENT." },
        source = { file = "Aggregates.xlsx", 
               directory = "%{DD.CoG_HISTORICAL}/emp_est/access_db_extracted"},
        target = { file = "StateGovtEmp_Aggregates.xlsx", 
                   directory = "%{env.local_task}/input/CoG_RAW/Historical" } },

    CoG_HISTORICAL_STATE_FIN | Link = 'dir {
        metadata = { description = "Census of Governments Historical Files: STATE FINANCE." },
        source = { directory = "%{DD.CoG_HISTORICAL}/State_Govt_Fin/access_db_extracted" },
        target = { directory = "%{env.local_task}/input/CoG_RAW/Historical/StateGovtFin_historical" } },

    CoG_HISTORICAL_CITY_FIN | Link = 'file {
        metadata = { description = "Census of Governments Historical Files: CITY FINANCE." },
        source = { file = "City_Govt_Finances.xlsx", 
               directory = "%{DD.CoG_HISTORICAL}/City_Govt_Fin/access_db_extracted"},
        target = { directory = "%{env.local_task}/input/CoG_RAW/Historical" } },

    CoG_HISTORICAL_COUNTY_FIN | Link = 'file {
        metadata = { description = "Census of Governments Historical Files: COUNTY FINANCE." },
        source = { file = "County_Govt_Finances.xlsx", 
               directory = "%{DD.CoG_HISTORICAL}/County_Govt_Fin/access_db_extracted"},
        target = { directory = "%{env.local_task}/input/CoG_RAW/Historical" } },

    CoG_GOVT_FIN | Link = 'dir {
        metadata = { description = "Census of Governments Historical Files: FINANCE." },
        source = { directory = "%{DD.CoG_HISTORICAL}/Govt_Fin/access_db_extracted" },
        target = { directory = "%{env.local_task}/input/CoG_RAW/Historical/Govt_Fin_historical" } },
    # -------------------------------------------------------------------------------------------- #


    # -------------------------------------------------------------------------------------------- #
    # -- COG IDS
    CoG_ID_2022 | Link = 'file {
        metadata = { description = "Census of Governments Cross Identifiers (2022)." },
        source = { file = "Govt_Units_2022_Final.xlsx", directory = "%{DD.CoG_RAW}/IdCodes"},
        target = { directory = "%{env.local_task}/input/id_codes" } },
        
    CoG_ID_INDFIN | Link = 'file {
        metadata = { description = "Census of Governments IndFin ID Directory." },
        source = { file = "ALLids.csv", directory = "%{DD.CoG_RAW}/IndFin"},
        target = { directory = "%{env.local_task}/input/id_codes" } },    
    # -------------------------------------------------------------------------------------------- #


    # -------------------------------------------------------------------------------------------- #
    # OTHER CENSUS STUFF
    CENSUS_POP_STATE | Link = 'file {
        metadata = { description = "Census of POPULATION." },
        source = { file = "CENSUS_POP_STATE.csv.gz", directory = "%{PD.IMPORT_OTHER}/output/CENSUS_POP"},
        target = { directory = "%{env.local_task}/input/other" } },

    NBER_RECESSIONS | Link = 'file {
        metadata = { description = "NBER_RECESSIONS." },
        source = { file = "NBER_recessions.csv", directory = "%{PD.IMPORT_OTHER}/output"},
        target = { directory = "%{env.local_task}/input/other" } },
    # -------------------------------------------------------------------------------------------- #


    # -------------------------------------------------------------------------------------------- #
    # -- other stuff ...
    TeXPreamble | Link = 'file {
        metadata = { description = "Standard TeX Preamble." },
        source = { file = "preamble.tex", directory = "%{rules_user.SYSTEM_DIRS.UTILITIES}/typesetting"},
        target = { directory = "%{env.local_task}/input/hand" } },
    # -------------------------------------------------------------------------------------------- #


} 
|> serialize_records

