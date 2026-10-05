# API Authentication & Security Tokens

> **BizFlow JWT Architecture**  
> *Bearer token lifecycle, refresh token rotation, revocation list, and FastAPI dependency injection.*

---

## 1. Token Architecture

BizFlow issues cryptographically signed JWT tokens conforming to RFC 7519:
- **Algorithm**: HMAC-SHA256 (`HS256`).
- **Access Token Lifetime**: 60 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES = 60`).
- **Refresh Token Lifetime**: 7 days (`REFRESH_TOKEN_EXPIRE_DAYS = 7`).
- **Token Claims**:
```json
{
  "sub": "user_id",
  "email": "user@bizflow.com",
  "role": "manager",
  "company_id": 1,
  "jti": "unique-token-uuid",
  "exp": 1790900000
}
```

---

## 2. FastAPI Dependency Injection (`get_current_user`)

Protected endpoints require the `get_current_user` dependency:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from core.security import decode_access_token
from apps.accounts.models import User, RevokedToken

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    # Revocation check
    if RevokedToken.objects.filter(token=token).exists():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
        
    user = User.objects.filter(id=payload.get("sub"), is_active=True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
```

---

## 3. Token Revocation Mechanism

When a user calls `POST /api/v1/auth/logout`:
1. The token is parsed for its expiration timestamp.
2. The raw token string or JTI is persisted into the `accounts_revokedtoken` table.
3. Subsequent requests presenting this token are denied with `HTTP 401 Unauthorized`.
4. A periodic scheduled cleanup task deletes expired entries from `RevokedToken` to keep the table compact.
