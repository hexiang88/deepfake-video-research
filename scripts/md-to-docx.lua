-- Rewrite Markdown links so Word hyperlinks still work after md→docx.
-- HTTP(S) links are kept. Same-document #anchors are kept.
-- Relative *.md links become relative *.docx (same folder tree as the export).
-- Other relative files become file:/// absolute URIs.

local function is_web_or_anchor(u)
  return u:match("^https?://") or u:match("^mailto:") or u:match("^#")
end

local function abs_path(p)
  if p:match("^%a:[/\\]") or p:match("^/") then
    return pandoc.path.normalize(p)
  end
  local cwd = pandoc.system.get_working_directory()
  return pandoc.path.normalize(pandoc.path.join({ cwd, p }))
end

local function to_file_uri(abs)
  abs = abs:gsub("\\", "/")
  if abs:match("^%a:") then
    return "file:///" .. abs
  end
  return "file://" .. abs
end

function Link(el)
  local target = el.target
  if target == nil or target == "" or is_web_or_anchor(target) then
    return el
  end

  local path, frag = target:match("^(.-)(#.*)$")
  if not path then
    path, frag = target, ""
  end

  local src = PANDOC_STATE.input_files and PANDOC_STATE.input_files[1]
  if not src then
    return el
  end

  local src_dir = pandoc.path.directory(abs_path(src))
  local abs = pandoc.path.normalize(pandoc.path.join({ src_dir, path }))
  local out_root = os.getenv("DOCX_OUT_ROOT")
  local src_root = os.getenv("DOCX_SRC_ROOT")

  if path:match("%.md$") and out_root and src_root then
    src_root = pandoc.path.normalize(src_root)
    out_root = pandoc.path.normalize(out_root)
    abs = abs:gsub("\\", "/")
    src_root = src_root:gsub("\\", "/")
    out_root = out_root:gsub("\\", "/")
    local prefix = src_root
    if prefix:sub(-1) ~= "/" then
      prefix = prefix .. "/"
    end
    if abs:sub(1, #prefix) == prefix then
      local rel = abs:sub(#prefix + 1):gsub("%.md$", ".docx")
      local dest_docx = pandoc.path.normalize(pandoc.path.join({ out_root, rel }))
      local this_out = os.getenv("DOCX_THIS_OUT")
      if this_out then
        local from_dir = pandoc.path.directory(this_out)
        el.target = pandoc.path.make_relative(dest_docx, from_dir):gsub("\\", "/") .. frag
        return el
      end
    end
  end

  el.target = to_file_uri(abs) .. frag
  return el
end
