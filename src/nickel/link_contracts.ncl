# =============================================================================
# link_contracts.ncl - Type contracts for data link definitions
# =============================================================================

# Contract for fields that can be String or Array of Strings
let StringOrArrayOfString =
  std.contract.any_of [String, Array String]
in

# Metadata type for link entries
let MetadataType = {
  type | String | optional,
  description | String | optional,
  generated_by | StringOrArrayOfString | optional,
  used_by | StringOrArrayOfString | optional,
}
in

# Link type enum variants
let LinkEnum = [|
  # Single file link
  'file {
    metadata = { type | String | default = "file" } | MetadataType,
    source = {
      file | String,
      directory | String,
      task | String | optional,
    },
    target = {
      file | String | default = source.file,
      directory | String,
    },
  },

  # Multiple files link
  'files {
    metadata = { type | String | default = "files" } | MetadataType,
    source = {
      file | Array String,
      directory | String,
      task | String | optional,
    },
    target = {
      file | Array String | default = source.file,
      directory | String,
    },
  },

  # Directory link
  'dir {
    metadata = { type | String | default = "directory" } | MetadataType,
    source = {
      directory | String,
      task | String | optional,
    },
    target = {
      directory | String | default = source.directory,
    },
  },
|]
in

# Serialize link records for JSON export
let _serialize_records = fun records =>
  records
  # Remove the not_exported env field
  |> std.record.filter (fun name _value => name != "env")
  # Convert enum variants to records with tag/arg
  |> std.record.map_values (fun x => std.enum.to_tag_and_arg x)
  # Extract source, target, metadata to top level
  |> std.record.map_values (fun x =>
       x
       |> std.record.insert_with_opts "source" x.arg.source
       |> std.record.insert_with_opts "target" x.arg.target
       |> std.record.insert_with_opts "metadata" x.arg.metadata
     )
  # Remove temporary fields
  |> std.record.map_values (fun x =>
       x
       |> std.record.remove_with_opts "arg"
       |> std.record.remove_with_opts "tag"
     )
in

# =============================================================================
# Exports
# =============================================================================
{
  link = LinkEnum,
  serialize_records = _serialize_records,
}
