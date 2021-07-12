# SPDX-FileCopyrightText: 2021 Malte Kliemann, Ole Kliemann
# 
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest import mock
import pytest

from drmock import types
from drmock import overload


@pytest.mark.parametrize('virtual_methods, access_specs, expected', [
    ([], None, []),
    ([types.Method(name='g', return_type='int', virtual=True, access='protected'),
      types.Method(name='g', return_type='int', params=['int'], virtual=True),
      types.Method(name='h', return_type='float', virtual=True),
      types.Method(name='h', return_type='float', params=['int'], virtual=True)],
     None,
     [overload.Overload(None,
                        [types.Method(name='g',
                                      return_type='int',
                                      params=['int'],
                                      virtual=True)]),
      overload.Overload(None,
                        [types.Method(name='h', return_type='float', virtual=True),
                         types.Method(name='h',
                                      return_type='float',
                                      params=['int'],
                                      virtual=True)])]),
    ([types.Method(name='g', return_type='int', virtual=True),
      types.Method(name='g', return_type='int', params=['int'], virtual=True, access='protected'),
      types.Method(name='h', return_type='float', virtual=True, access='protected'),
      types.Method(name='h', return_type='float', params=['int'], virtual=True, access='private')],
     ['protected', 'private'],
     [overload.Overload(None,
                        [types.Method(name='g',
                                      return_type='int',
                                      params=['int'],
                                      virtual=True,
                                      access='protected')]),
      overload.Overload(None,
                        [types.Method(name='h', return_type='float', virtual=True, access='protected'),
                         types.Method(name='h',
                                      return_type='float',
                                      params=['int'],
                                      virtual=True,
                                      access='private')])])
])
def test_get_overloads_of_class(virtual_methods, access_specs, expected, mocker):
    class_ = mocker.Mock(get_virtual_methods=mocker.Mock(return_value=virtual_methods))
    result = overload.get_overloads_of_class(class_, access_specs)
    for r, e in zip(result, expected):
        assert r._methods == e._methods


class TestOverload:

    @pytest.mark.parametrize('parent, kwargs, expected', [
        ('Foo',
         [{'mangled_name': mock.Mock(return_value='foo'), 'params': [], 'const': True},
          {'mangled_name': mock.Mock(return_value='foo'), 'params': ['int'], 'const': False}],
         types.Method(name='foo',
                      return_type=types.Type(inner='auto', lvalue_ref=True),
                      template=types.TemplateDecl(['... DRMOCK_Ts']),
                      body='return foo_dispatch(TypeContainer<DRMOCK_Ts ...>{});')),
        ('Foo',
         [{'mangled_name': mock.Mock(return_value='foo'), 'params': [
             'int', 'float'], 'const': True}],
         types.Method(
             name='foo',
             return_type=types.Type(inner='auto', lvalue_ref=True),
             template=types.TemplateDecl(['... DRMOCK_Ts']),
             body='return foo_dispatch(TypeContainer<DRMOCK_Ts ..., int, float, drmock::Const>{});')),
        ('Foo',
         [{'mangled_name': mock.Mock(return_value='foo'), 'params': [], 'const': True},
          {'mangled_name': mock.Mock(return_value='foo'), 'params': ['int'], 'const': True}],
         types.Method(name='foo',
                      return_type=types.Type(inner='auto', lvalue_ref=True),
                      template=types.TemplateDecl(['... DRMOCK_Ts']),
                      body='return foo_dispatch(TypeContainer<DRMOCK_Ts ..., drmock::Const>{});')),
    ])
    def test_generate_getter(self, parent, kwargs, expected, mocker):
        methods = [mocker.Mock(**each) for each in kwargs]
        collection = overload.Overload(parent, methods)
        assert collection.generate_getter() == expected

    @pytest.mark.parametrize('full_name, kwargs, expected', [
        ('Foo',
         [{'mangled_name': mock.Mock(return_value='foo'),
           'params': [], 'const': True, 'return_type': 'int'},
          {'mangled_name': mock.Mock(return_value='foo'),
           'params': [types.Type('float')],
           'const': False,
           'return_type': 'int'}],
         [types.Variable(name='METHODS_DRMOCK_foo_0',
                         type='std::shared_ptr<Method<Foo, int>>',
                         default_args=[
                             'std::make_shared<Method<Foo, int>>("", STATE_OBJECT_DRMOCK_)'],
                         access='private'),
          types.Variable(name='METHODS_DRMOCK_foo_1',
                         type='std::shared_ptr<Method<Foo, int, float>>',
                         default_args=[
                             'std::make_shared<Method<Foo, int, float>>("", STATE_OBJECT_DRMOCK_)'],
                         access='private')]),
        ('Bar',
         [{'mangled_name': mock.Mock(return_value='bar'),
           'params': [types.Type('int'), types.Type('float')],
           'const': True,
           'return_type': 'void'}],
         [types.Variable(name='METHODS_DRMOCK_bar_0',
                         type='std::shared_ptr<Method<Bar, void, int, float>>',
                         default_args=[
                             'std::make_shared<Method<Bar, void, int, float>>("", STATE_OBJECT_DRMOCK_)'],
                         access='private')]),
        ('Baz',
         [{'mangled_name': mock.Mock(return_value='baz'),
           'params': [],
           'const': True,
           'return_type': 'const int&'},
          {'mangled_name': mock.Mock(return_value='baz'),
           'params': [types.Type('int', lvalue_ref=True)],
           'const': True,
           'return_type': 'const int&'}],
         [types.Variable(name='METHODS_DRMOCK_baz_0',
                         type='std::shared_ptr<Method<Baz, const int&>>',
                         default_args=[
                             'std::make_shared<Method<Baz, const int&>>("", STATE_OBJECT_DRMOCK_)'],
                         access='private'),
          types.Variable(name='METHODS_DRMOCK_baz_1',
                         type='std::shared_ptr<Method<Baz, const int&, int>>',
                         default_args=[
                             'std::make_shared<Method<Baz, const int&, int>>("", STATE_OBJECT_DRMOCK_)'],
                         access='private')]),
    ])
    def test_generate_shared_ptrs(self, full_name, kwargs, expected, mocker):
        parent = mocker.Mock(full_name=mocker.Mock(return_value=full_name))
        methods = [mocker.Mock(**each) for each in kwargs]
        collection = overload.Overload(parent, methods)
        assert collection.generate_shared_ptrs() == expected

    @pytest.mark.parametrize('full_name, kwargs, expected', [
        ('Foo',
         [{'mangled_name': mock.Mock(return_value='foo'),
           'params': [],
           'const': True,
           'volatile': False},
          {'mangled_name': mock.Mock(return_value='foo'),
           'params': ['int'],
           'const': False,
           'volatile': False}],
         [types.Method(name='foo_dispatch',
                       params=[types.Type(inner='TypeContainer<drmock::Const>')],
                       return_type=types.Type(inner='auto', lvalue_ref=True),
                       body='return *METHODS_DRMOCK_foo_0;',
                       access='private'),
          types.Method(name='foo_dispatch',
                       params=[types.Type(inner='TypeContainer<int>')],
                       return_type=types.Type(inner='auto', lvalue_ref=True),
                       body='return *METHODS_DRMOCK_foo_1;',
                       access='private')]),
        ('Bar',
         [{'mangled_name': mock.Mock(return_value='foo'),
           'params': ['int', 'float'],
           'const': True,
           'volatile': False}],
         [types.Method(name='foo_dispatch',
                       params=[types.Type(inner='TypeContainer<int, float, drmock::Const>')],
                       return_type=types.Type(inner='auto', lvalue_ref=True),
                       body='return *METHODS_DRMOCK_foo_0;',
                       access='private')]),
        ('Baz',
         [{'mangled_name': mock.Mock(return_value='baz'),
           'params': [],
           'const': True,
           'volatile': False},
          {'mangled_name': mock.Mock(return_value='baz'),
           'params': ['int'],
           'const': True,
           'volatile': False}],
         [types.Method(name='baz_dispatch',
                       params=[types.Type(inner='TypeContainer<drmock::Const>')],
                       return_type=types.Type(inner='auto', lvalue_ref=True),
                       body='return *METHODS_DRMOCK_baz_0;',
                       access='private'),
          types.Method(name='baz_dispatch',
                       params=[types.Type(inner='TypeContainer<int, drmock::Const>')],
                       return_type=types.Type(inner='auto', lvalue_ref=True),
                       body='return *METHODS_DRMOCK_baz_1;',
                       access='private')])
    ])
    def test_generate_dispatch_methods(self, full_name, kwargs, expected, mocker):
        parent = mocker.Mock(full_name=mocker.Mock(return_value=full_name))
        methods = [mocker.Mock(**each) for each in kwargs]
        collection = overload.Overload(parent, methods)
        assert collection.generate_dispatch_methods() == expected

    @pytest.mark.parametrize('methods, expected', [
        ([types.Method(name='bar', params=[types.Type('int')], virtual=True,
                       const=True, return_type=types.Type('int'), body='return 0;')],
         [types.Method(name='bar', params=['int a0'], override=True,
                       const=True, return_type=types.Type('int'),
                       body=('auto& result = *mock.bar().call(std::move(a0));\n'
                             'return std::forward<int>(drmock::moveIfNotCopyConstructible(result));'))]),
        ([types.Method(name='operator<=', params=[types.Type('int'), types.Type('int')],
                       return_type=types.Type('bool'), body='...', virtual=True)],
         [types.Method(name='operator<=', params=['int a0', 'int a1'],
                       return_type=types.Type('bool'), override=True,
                       body=('auto& result = *mock.operatorLesserOrEqual().call(std::move(a0), std::move(a1));\n'
                             'return std::forward<bool>(drmock::moveIfNotCopyConstructible(result));'))]),
        ([types.Method(name='bar', return_type=types.Type('void'),
                       const=False,
                       volatile=False),
          types.Method(name='bar', return_type=types.Type('void'),
                       const=True,
                       volatile=False),
          types.Method(name='bar', return_type=types.Type('void'),
                       const=False,
                       volatile=True),
          types.Method(name='bar', return_type=types.Type('void'),
                       const=True,
                       volatile=True)],
         [types.Method(name='bar', return_type=types.Type('void'), override=True,
                       const=False,
                       volatile=False,
                       body=('mock.template bar<>().call();')),
          types.Method(name='bar', return_type=types.Type('void'), override=True,
                       const=True,
                       volatile=False,
                       body=('mock.template bar<drmock::Const>().call();')),
          types.Method(name='bar', return_type=types.Type('void'), override=True,
                       const=False,
                       volatile=True,
                       body=('mock.template bar<drmock::Volatile>().call();')),
          types.Method(name='bar', return_type=types.Type('void'), override=True,
                       const=True,
                       volatile=True,
                       body=('mock.template bar<drmock::Const, drmock::Volatile>().call();'))]),
        ([types.Method(name='bar',
                       params=[types.Type('int')],
                       virtual=True,
                       return_type=types.Type('void'),
                       body='std::cout << "foo" << std::endl;'),
          types.Method(name='bar',
                       return_type=types.Type('void'),
                       body='std::cout << "foo" << std::endl;')],
         [types.Method(name='bar',
                       override=True,
                       params=['int a0'],
                       return_type=types.Type('void'),
                       body='mock.template bar<int>().call(std::move(a0));'),
          types.Method(name='bar',
                       override=True,
                       return_type=types.Type('void'),
                       body='mock.template bar<>().call();')]),
        ([types.Method(name='foo',
                       const=False,
                       virtual=True,
                       pure_virtual=True,
                       params=[types.Type.from_spelling('int'),
                               types.Type.from_spelling('const float &'),
                               types.Type.from_spelling('std::vector<double> &&')],
                       return_type=types.Type.from_spelling('int &'),
                       body='return & value_;'),
          types.Method(name='foo',
                       const=True,
                       virtual=True,
                       params=[types.Type.from_spelling('const float &'),
                               types.Type.from_spelling('Ts && ...')],
                       return_type=types.Type.from_spelling('const int &'),
                       body='return & value_;')],
         [types.Method(name='foo',
                       return_type=types.Type(inner='int', lvalue_ref=True),
                       params=['int a0', 'const float & a1', 'std::vector<double> && a2'],
                       override=True,
                       body=('auto& result = *mock.template foo<int, const float &, std::vector<double> &&>().call(std::move(a0), a1, std::move(a2));\n'
                             'return std::forward<int &>(drmock::moveIfNotCopyConstructible(result));')),
          types.Method(name='foo',
                       const=True,
                       return_type=types.Type.from_spelling('const int &'),
                       params=['const float & a0', 'Ts && ... a1'],
                       override=True,
                       body=('auto& result = *mock.template foo<const float &, Ts && ..., drmock::Const>().call(a0, std::move(a1)...);\n'
                             'return std::forward<const int &>(drmock::moveIfNotCopyConstructible(result));'))]),
    ])
    def test_generate_mock_implementations(self, methods, expected):
        collection = overload.Overload(None, methods)
        assert collection.generate_mock_implementations() == expected

    @pytest.mark.parametrize('is_overload, kwargs, expected', [
        (False,
         [{'mangled_name': mock.Mock(return_value='foo_mangled'),
           'params': ['int', 'float', 'double'], 'const': False, 'volatile': False}],
         ['mock.foo_mangled().parent(this);']),
        (False,
         [{'mangled_name': mock.Mock(return_value='foo_mangled'),
           'params': ['int', 'float', 'double'], 'const': True, 'volatile': False}],
         ['mock.foo_mangled().parent(this);']),
        (True,
         [{'mangled_name': mock.Mock(return_value='foo_mangled'),
           'params': ['int', 'float', 'double'], 'const': True, 'volatile': False},
          {'mangled_name': mock.Mock(return_value='foo_mangled'),
           'params': ['std::unordered_map<int, float>'], 'const': False, 'volatile': False}],
         ['mock.template foo_mangled<int, float, double, drmock::Const>().parent(this);',
          'mock.template foo_mangled<std::unordered_map<int, float>>().parent(this);']),
    ])
    def test_generate_set_parent(self, is_overload, kwargs, expected, mocker):
        parent = mocker.Mock(is_overload=mocker.Mock(return_value=is_overload))
        methods = [mocker.Mock(**each) for each in kwargs]
        collection = overload.Overload(parent, methods)
        assert collection.generate_set_parent() == expected
