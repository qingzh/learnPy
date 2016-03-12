from .common import AttributeDict
from ..exceptions import DBQueryException


QADB = AttributeDict(
    host='10.99.60.76',
    user='admin',
    passwd='3tdnk2Z1Ak',
    db='wolong_0003',
    charset='utf8',
    use_unicode=True,
)


def get_db_uid(username):
    # get suffix of TDDL, and uid
    for i in xrange(8):
        suffix = '000%d' % i
        with db.connect(**QADB(db='wolong_%s' % suffix)) as cur:
            cur.execute(
                "select id from tb_account_%s where name='%s';"
                 % (suffix, username)
            )
            ret = cur.fetchone()
        if ret:
            return ret[0]
    raise DBQueryException('No Such User%s' % username)
