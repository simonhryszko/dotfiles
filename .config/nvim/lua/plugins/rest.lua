if true then
  return {}
end

return {
  "rest-nvim/rest.nvim",
  dependencies = {
    "nvim-treesitter/nvim-treesitter",
    opts = function(_, opts)
      opts.ensure_installed = opts.ensure_installed or {}
      opts.rocks.enabled = false
      table.insert(opts.ensure_installed, "http")
    end,
  },
}
