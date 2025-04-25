return {
  servers = {
    pylsp = {
      settings = {
        pylsp = {
          plugins = {
            autopep8 = {
              enabled = false, -- disable autopep8
              ignore = { "E203" }, -- Disable the leading comma rule (E203)
            },
            pycodestyle = {
              enabled = false, -- disable autopep8
              ignore = { "E501" },
            },
            pyflakes = {
              enabled = false,
            },
          },
        },
      },
    },
  },
}
