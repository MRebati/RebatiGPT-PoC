import { useRecoilValue } from 'recoil';

import { Stack, Typography } from '@mui/material';

import { Translator } from 'components/i18n';

import 'assets/logo_dark.svg';
import LogoDark from 'assets/logo_dark.svg?react';
import 'assets/logo_light.svg';
import LogoLight from 'assets/logo_light.svg?react';

import { settingsState } from 'state/settings';

export default function WaterMark() {
  const { theme } = useRecoilValue(settingsState);
  const Logo = theme === 'light' ? LogoLight : LogoDark;
  return (
    <Stack mx="auto" className="watermark">
      <a
        href="https://rebati.net"
        target="_blank"
        style={{
          display: 'flex',
          alignItems: 'center',
          textDecoration: 'none',
          lineHeight: '1.4em',
          height: '1.4em',
          verticalAlign: 'baseline',
          paddingLeft: '4px',
        }}
      >
        <Typography fontSize="12px" color="text.secondary">
          <Translator path="components.organisms.chat.inputBox.waterMark.text" />
        </Typography>
        <Logo
          style={{
            width: 65,
            height: '1.5em',
            filter: 'grayscale(1)',
            paddingRight: '4px'
          }}
        />
      </a>
    </Stack>
  );
}
